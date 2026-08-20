export function getServerEnv() {
  return {
    backendApiUrl: process.env.BACKEND_API_URL ?? "",
    masterdataApiUrl: process.env.MASTERDATA_API_URL ?? "",
    loginProviderId: process.env.LOGIN_PROVIDER_ID ?? "",
    applicationMnemonic: process.env.APPLICATION_MNEMONIC ?? "iam-staff-ui",
    cookieDomain: process.env.COOKIE_DOMAIN?.trim() ?? "",
    pageSize: parseInt(process.env.PAGE_SIZE ?? "10", 10),
  };
}

export type ServerEnv = ReturnType<typeof getServerEnv>;
