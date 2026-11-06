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
      header: t("name"),
      render: (lp: LoginProvider) => lp.provider_name,
    },
    {
      key: "clientId",
      header: t("clientId"),
      render: (lp: LoginProvider) => lp.client_id,
    },
    {
      key: "issuer",
      header: t("issuer"),
      render: (lp: LoginProvider) => lp.issuer,
    },
    {
      key: "authMethod",
      header: t("authMethod"),
      render: (lp: LoginProvider) => lp.token_endpoint_auth_method || "—",
    },
    {
      key: "status",
      header: t("status"),
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
      header: t("actions"),
      render: (lp: LoginProvider) => (
        <Can action="loginProvider:delete">
          <DeleteButton
            onClick={() => onDelete(lp)}
            title={t("deleteLoginProvider")}
          >
            {t("delete")}
          </DeleteButton>
        </Can>
      ),
    },
  ];
}
