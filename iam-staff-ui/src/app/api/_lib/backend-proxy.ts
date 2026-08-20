import "server-only";
import { randomUUID } from "crypto";
import { NextRequest, NextResponse } from "next/server";
import { CSRF_COOKIE_NAME, CSRF_HEADER_NAME } from "@/shared/utils/csrf";
import { getBackendConfig } from "./backend-config";
import { BackendResponse, RequestBody } from "./backend-types";
import { createBackendRequest } from "./backend-request";
import { requireAuth } from "./requireAuth";
import { applyBackendSetCookies } from "./auth-cookies";

function isHttpUrl(value: string): boolean {
  try {
    const parsed = new URL(value);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

/** Registry staff API: Bearer token plus a matching CSRF cookie/header pair. */
function registryUpstreamHeaders(accessToken: string, csrfToken: string): Record<string, string> {
  return {
    "Content-Type": "application/json",
    accept: "application/json",
    Authorization: `Bearer ${accessToken}`,
    [CSRF_HEADER_NAME]: csrfToken,
    Cookie: `${CSRF_COOKIE_NAME}=${csrfToken}`,
  };
}

export type PayloadBuilder = (body: any) => RequestBody;
export type ResponseTransformer = (responseBody: any) => any;

interface BackendProxyOptions {
  req: NextRequest;
  targetEndpoint: string;
  buildPayload?: PayloadBuilder;
  transformResponse?: ResponseTransformer;
  caching?: RequestInit;
  responseHeaders?: HeadersInit;
  backendUrl?: string;
  backend?: "default" | "masterdata" | "registry";
}

const errorCodeMap: Record<string, number> = {
  "G2P-AUT-401": 401,
  "G2P-AUT-403": 403,
  "G2P-AUT-404": 404,
};

/** Default unwrap: response_payload + pagination_response when present. */
export function unwrapResponseBody(responseBody: any) {
  if (!responseBody) return undefined;
  if (responseBody.pagination_response != null) {
    return {
      items: responseBody.response_payload,
      pagination: responseBody.pagination_response,
    };
  }
  return responseBody.response_payload;
}

export async function proxyToBackend({
  req,
  targetEndpoint,
  buildPayload,
  transformResponse,
  caching,
  responseHeaders,
  backendUrl: customBackendUrl,
  backend,
}: BackendProxyOptions) {
  const backendConfig = getBackendConfig();
  const auth = requireAuth(req);
  if (auth instanceof NextResponse) return auth;

  try {
    let body: any = {};
    if (req.method !== "GET") {
      try {
        body = await req.json();
      } catch {
        // empty body
      }
    }

    const host = req.headers.get("x-forwarded-host") || req.headers.get("host");
    const proto = req.headers.get("x-forwarded-proto") || "https";
    const origin = req.headers.get("origin") || `${proto}://${host}`;

    let baseUrl;
    let upstreamHeaders: Record<string, string> = {
      ...auth.backendHeaders,
      "Content-Type": "application/json",
    };
    if (customBackendUrl) {
      baseUrl = customBackendUrl;
    } else if (backend === "masterdata") {
      baseUrl = backendConfig.masterdataApiUrl;
    } else if (backend === "registry") {
      const apiUrl =
        typeof body?.api_url === "string"
          ? body.api_url.trim().replace(/\/+$/, "")
          : "";
      if (!apiUrl || !isHttpUrl(apiUrl)) {
        return NextResponse.json(
          {
            error:
              "api_url is required to call the registry API. Set it on the application.",
          },
          { status: 400 },
        );
      }
      baseUrl = apiUrl;
      const csrfToken =
        (typeof body?.csrf_token === "string" && body.csrf_token.trim()) ||
        req.headers.get(CSRF_HEADER_NAME) ||
        randomUUID();
      upstreamHeaders = registryUpstreamHeaders(auth.accessToken, csrfToken);
      if (body && typeof body === "object") {
        const rest = { ...body };
        delete rest.api_url;
        delete rest.csrf_token;
        delete rest.access_token;
        body = rest;
      }
    } else {
      baseUrl = backendConfig.backendApiUrl;
    }

    const backendUrl = `${baseUrl}${targetEndpoint}`;

    const defaultPayloadBuilder: PayloadBuilder = (b) => {
      const { current_page, page_size, ...rest } = b || {};
      return {
        pagination_request: (current_page !== undefined || page_size !== undefined)
          ? { current_page: current_page || 1, page_size: page_size || 20 }
          : undefined,
        request_payload: rest ?? {},
      };
    };

    const payload = (buildPayload || defaultPayloadBuilder)(body);

    const backendRequest = createBackendRequest(payload, origin);

    const response = await fetch(backendUrl, {
      method: "POST",
      ...caching,
      headers: upstreamHeaders,
      body: JSON.stringify(backendRequest),
    });

    const backendResponse: BackendResponse = await response.json();

    if (backendResponse.response_header?.response_status === "ERROR") {
      const errorCode = backendResponse.response_header.response_error_code;
      const status = errorCodeMap[errorCode] || 400;

      const errorResponse = NextResponse.json(
        {
          error: backendResponse.response_header.response_error_message,
          code: errorCode,
        },
        {
          status,
          headers: responseHeaders,
        },
      );
      applyBackendSetCookies(response, errorResponse);
      return errorResponse;
    }

    const responseBody = backendResponse.response_body;
    const data = transformResponse
      ? transformResponse(responseBody)
      : unwrapResponseBody(responseBody);

    if (data === undefined) {
      const emptyResponse = NextResponse.json(
        { error: "Empty response from backend" },
        { status: 500, headers: responseHeaders },
      );
      applyBackendSetCookies(response, emptyResponse);
      return emptyResponse;
    }

    const successResponse = NextResponse.json(data, {
      headers: responseHeaders,
    });
    applyBackendSetCookies(response, successResponse);
    return successResponse;
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Internal Server Error" },
      { status: 500 },
    );
  }
}
