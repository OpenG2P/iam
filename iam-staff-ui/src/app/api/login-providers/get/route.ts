import { NextRequest } from "next/server";
import { proxyToBackend } from "@/app/api/_lib/backend-proxy";

export async function POST(req: NextRequest) {
  return proxyToBackend({
    req,
    targetEndpoint: "/login-providers/get_login_provider",
    buildPayload: (body) => ({
      request_payload: { id: body?.id },
    }),
  });
}
