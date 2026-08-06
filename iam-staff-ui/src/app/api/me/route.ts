import { NextRequest, NextResponse } from "next/server";
import { requireAuth } from "../_lib/requireAuth";
import { getBackendConfig } from "../_lib/backend-config";
import { jsonResponseFromBackend } from "../_lib/auth-cookies";

export async function GET(req: NextRequest) {
  const auth = requireAuth(req);
  if (auth instanceof NextResponse) return auth;

  const backendConfig = getBackendConfig();
  const res = await fetch(`${backendConfig.backendApiUrl}/auth/get_user_profile`, {
    method: "GET",
    headers: auth.backendHeaders,
    cache: "no-store",
  });

  return jsonResponseFromBackend(res);
}
