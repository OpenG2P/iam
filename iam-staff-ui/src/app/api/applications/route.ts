import { NextRequest } from "next/server";
import { proxyToBackend } from "@/app/api/_lib/backend-proxy";
import { getBackendConfig } from "@/app/api/_lib/backend-config";

export async function POST(req: NextRequest) {
  const { pageSize } = getBackendConfig();
  return proxyToBackend({
    req,
    targetEndpoint: "/applications/get_applications",
    buildPayload: (body) => ({
      pagination_request: {
        current_page: body?.current_page ?? 1,
        page_size: body?.page_size ?? pageSize,
        sort_by: body?.sort_by,
        search_text: body?.search_text,
      },
      request_payload: body?.request_payload ?? {},
    }),
  });
}
