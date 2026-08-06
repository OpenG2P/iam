import { NextRequest } from "next/server";
import { proxyToBackend } from "@/app/api/_lib/backend-proxy";

export async function POST(req: NextRequest) {
  return proxyToBackend({
    req,
    targetEndpoint: "/data-policies/get_all_policies",
    buildPayload: (body) => ({
      pagination_request: {
        current_page: body?.current_page ?? 1,
        page_size: body?.page_size ?? 10,
        sort_by: body?.sort_by ?? "",
        filter_by: body?.filter_by ?? "",
        search_text: body?.search_text ?? "",
      },
      request_payload: {
        application_id: body?.application_id,
        policy_target: body?.policy_target,
        register_id: body?.register_id,
      },
    }),
    transformResponse: (responseBody) => ({
      policies: responseBody?.response_payload?.policies || [],
      pagination: responseBody?.pagination_response,
    }),
  });
}
