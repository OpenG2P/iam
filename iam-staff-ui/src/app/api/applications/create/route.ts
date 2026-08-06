import { NextRequest } from "next/server";
import { proxyToBackend } from "@/app/api/_lib/backend-proxy";

export async function POST(req: NextRequest) {
  return proxyToBackend({
    req,
    targetEndpoint: "/applications/create_application",
  });
}
