import { NextRequest } from "next/server";
import { proxyToBackend } from "@/app/api/_lib/backend-proxy";

export async function POST(req: NextRequest) {
  return proxyToBackend({
    req,
    targetEndpoint: "/applications/create_data_policy",
    buildPayload: (body) => ({
      request_payload: {
        application_id: body?.application_id,
        data_policy_mnemonic: body?.data_policy_mnemonic,
        role_description: body?.role_description,
      },
    }),
  });
}
