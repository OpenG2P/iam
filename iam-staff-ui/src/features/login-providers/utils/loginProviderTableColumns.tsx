import { Can, DeleteButton, StatusBadge } from "@/components";

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
        <StatusBadge
          active={lp.active}
          activeLabel={t("active")}
          inactiveLabel={t("inactive")}
        />
      ),
    },
    {
      key: "actions",
      header: "Actions",
      render: (lp: LoginProvider) => (
        <Can action="loginProvider:delete">
          <DeleteButton
            onClick={() => onDelete(lp)}
            title="Delete login provider"
          >
            {t("delete")}
          </DeleteButton>
        </Can>
      ),
    },
  ];
}
