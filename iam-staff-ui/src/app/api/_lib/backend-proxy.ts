import "server-only";
import { NextRequest, NextResponse } from "next/server";
import { getBackendConfig } from "./backend-config";
import { BackendResponse, RequestBody } from "./backend-types";
import { createBackendRequest } from "./backend-request";
import { requireAuth } from "./requireAuth";
import { applyBackendSetCookies } from "./auth-cookies";

export type PayloadBuilder = (body: any) => RequestBody;
export type ResponseTransformer = (responseBody: any) => any;

interface BackendProxyOptions {
  req: NextRequest;
  targetEndpoint: string;
  buildPayload?: PayloadBuilder;
  transformResponse?: ResponseTransformer;
  caching?: RequestInit;
  responseHeaders?: HeadersInit;
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

    const backendUrl = `${backendConfig.backendApiUrl}${targetEndpoint}`;

    const defaultPayloadBuilder: PayloadBuilder = (b) => ({
      pagination_request: undefined,
      request_payload: b ?? {},
    });

    const payload = (buildPayload || defaultPayloadBuilder)(body);

    const h = req.headers;
    const host = h.get("x-forwarded-host") || h.get("host");
    const proto = h.get("x-forwarded-proto") || "https";
    const origin = h.get("origin") || `${proto}://${host}`;

    const backendRequest = createBackendRequest(payload, origin);

    const response = await fetch(backendUrl, {
      method: "POST",
      ...caching,
      headers: {
        ...auth.backendHeaders,
        "Content-Type": "application/json",
      },
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
