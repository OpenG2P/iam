import { NextRequest } from "next/server";
import { proxyToBackend } from "@/app/api/_lib/backend-proxy";
import { getBackendConfig } from "@/app/api/_lib/backend-config";

export async function POST(req: NextRequest) {
  const { pageSize } = getBackendConfig();
  return proxyToBackend({
    req,
    targetEndpoint: "/applications/get_data_policies",
    buildPayload: (body) => ({
      pagination_request: {
        current_page: body?.current_page ?? 1,
        page_size: body?.page_size ?? pageSize,
      },
      request_payload: { application_id: body?.application_id },
    }),
  });
}
