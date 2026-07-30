import { NextRequest } from "next/server";
import { proxyToBackend } from "@/app/api/_lib/backend-proxy";

export async function POST(req: NextRequest) {
  return proxyToBackend({
    req,
    targetEndpoint: "/applications/delete_role",
    buildPayload: (body) => ({
      request_payload: {
        application_id: body?.application_id,
        id: body?.id,
      },
    }),
  });
}
