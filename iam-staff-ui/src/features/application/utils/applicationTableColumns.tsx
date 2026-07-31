import { Can } from "@/components";

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
      header: "Mnemonic",
      render: (app: Application) => app.application_mnemonic,
    },
    {
      key: "description",
      header: "Description",
      render: (app: Application) => app.application_description || "—",
    },
    {
      key: "url",
      header: "URL",
      render: (app: Application) => app.application_url || "—",
    },
    {
      key: "status",
      header: "Status",
      render: (app: Application) => (
        <span
          className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-medium ${app.active !== false ? "bg-[rgba(39,174,96,0.12)] text-[#27ae60]" : "bg-[rgba(196,196,196,0.3)] text-gray-600"}`}
        >
          {app.active !== false ? t("active") : t("inactive")}
        </span>
      ),
    },
    {
      key: "actions",
      header: "Actions",
      render: (app: Application) => (
        <Can action="application:delete">
          <button
            type="button"
            className="inline-block text-[16px] font-medium px-3 py-1.5 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-[rgba(192,57,43,0.1)] text-[#c0392b] hover:bg-[rgba(192,57,43,0.2)] disabled:opacity-50 disabled:not-allowed"
            onClick={(e) => {
              e.stopPropagation();
              onDelete(app);
            }}
            disabled={app.is_self_registered}
            title={app.is_self_registered ? "Cannot delete self-registered applications" : "Delete application"}
          >
            {t("delete")}
          </button>
        </Can>
      ),
    },
  ];
}
