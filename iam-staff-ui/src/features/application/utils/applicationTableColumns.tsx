import { Can, DeleteButton, StatusBadge } from "@/components";

interface Application {
  id: number;
  application_mnemonic: string;
  application_description?: string | null;
  application_url?: string | null;
  active?: boolean;
  is_self_registered?: boolean;
  order?: number | null;
}

interface ApplicationTableColumnsProps {
  onDelete: (app: Application) => void;
  t: any;
}

export function getApplicationColumns({
  onDelete,
  t,
}: ApplicationTableColumnsProps) {
  return [
    {
      key: "mnemonic",
      header: t("mnemonic"),
      render: (app: Application) => app.application_mnemonic,
    },
    {
      key: "description",
      header: t("description"),
      render: (app: Application) => app.application_description || "—",
    },
    {
      key: "url",
      header: t("url"),
      render: (app: Application) => app.application_url || "—",
    },
    {
      key: "status",
      header: t("status"),
      render: (app: Application) => (
        <StatusBadge
          active={app.active}
          activeLabel={t("active")}
          inactiveLabel={t("inactive")}
        />
      ),
    },
    {
      key: "actions",
      header: t("actions"),
      render: (app: Application) => (
        <Can action="application:delete">
          <DeleteButton
            onClick={() => onDelete(app)}
            disabled={app.is_self_registered}
            title={app.is_self_registered ? t("cannotDeleteSelfRegistered") : t("deleteApplication")}
          >
            {t("delete")}
          </DeleteButton>
        </Can>
      ),
    },
  ];
}
