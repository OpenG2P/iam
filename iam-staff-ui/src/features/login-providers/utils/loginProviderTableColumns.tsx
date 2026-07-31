import { Can } from "@/components";

interface LoginProvider {
  id: number;
  provider_name: string;
  description?: string | null;
  client_id: string;
  issuer: string;
  active?: boolean;
  token_endpoint_auth_method?: string;
}

interface LoginProviderTableColumnsProps {
  onDelete: (lp: LoginProvider) => void;
  t: any;
}

export function getLoginProviderColumns({
  onDelete,
  t,
}: LoginProviderTableColumnsProps) {
  return [
    {
      key: "name",
      header: "Name",
      render: (lp: LoginProvider) => lp.provider_name,
    },
    {
      key: "clientId",
      header: "Client ID",
      render: (lp: LoginProvider) => lp.client_id,
    },
    {
      key: "issuer",
      header: "Issuer",
      render: (lp: LoginProvider) => lp.issuer,
    },
    {
      key: "authMethod",
      header: "Auth Method",
      render: (lp: LoginProvider) => lp.token_endpoint_auth_method || "—",
    },
    {
      key: "status",
      header: "Status",
      render: (lp: LoginProvider) => (
        <span
          className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${lp.active !== false ? "bg-[rgba(39,174,96,0.12)] text-[#27ae60]" : "bg-[rgba(196,196,196,0.3)] text-gray-600"}`}
        >
          {lp.active !== false ? t("active") : t("inactive")}
        </span>
      ),
    },
    {
      key: "actions",
      header: "Actions",
      render: (lp: LoginProvider) => (
        <Can action="loginProvider:delete">
          <button
            type="button"
            className="inline-block text-[16px] font-medium px-3 py-1.5 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-[rgba(192,57,43,0.1)] text-[#c0392b] hover:bg-[rgba(192,57,43,0.2)] disabled:opacity-50 disabled:not-allowed"
            onClick={(e) => {
              e.stopPropagation();
              onDelete(lp);
            }}
            title="Delete login provider"
          >
            {t("delete")}
          </button>
        </Can>
      ),
    },
  ];
}
