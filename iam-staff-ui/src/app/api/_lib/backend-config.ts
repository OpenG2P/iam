import "server-only";

import { getServerEnv } from "./env-config";

export function getBackendConfig() {
  const env = getServerEnv();

  return {
    backendApiUrl: env.backendApiUrl,
    loginProviderId: env.loginProviderId,
    applicationMnemonic: env.applicationMnemonic,
    cookieDomain: env.cookieDomain,
    pageSize: env.pageSize,
  };
}
