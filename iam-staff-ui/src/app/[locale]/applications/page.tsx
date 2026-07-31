"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";
import { useFetch } from "@/shared/hooks/useFetch";
import { toast } from "react-toastify";
import Can from "@/components/Can";
import AddButton from "@/components/AddButton";
import ConfirmModal from "@/components/ConfirmModal";
import IconBase64Field from "@/components/IconBase64Field";
import Modal from "@/components/Modal";
import Pagination from "@/components/Pagination";
import Table from "@/components/Table";
import TableSkeleton from "@/components/TableSkeleton";
import { useConfig } from "@/context/ConfigContext";

const emptyForm = {
  application_mnemonic: "",
  application_description: "",
  application_url: "",
  order: "",
  width: "",
  icon_base64: "",
  icon_mime_type: "image/png",
};

interface Application {
  id: number;
  application_mnemonic: string;
  application_description?: string | null;
  application_url?: string | null;
  active?: boolean;
  is_self_registered?: boolean;
  order?: number | null;
}

interface ListResponse {
  items?: Application[];
  pagination?: {
    current_page?: number;
    page_size?: number;
    number_of_items?: number;
  };
  error?: string;
}

export default function ApplicationsPage() {
  const t = useTranslations();
  const { pageSize } = useConfig();
  const router = useRouter();
  const { execute } = useFetch<ListResponse>();
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<Application[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadedOnce, setLoadedOnce] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<Application | null>(null);
  const [deleting, setDeleting] = useState(false);
  const loadSeq = useRef(0);

  const load = useCallback(
    async (p: number) => {
      const seq = ++loadSeq.current;
      setLoading(true);
      setError(null);
      try {
        const data = await execute("/api/applications", {
          method: "POST",
          body: JSON.stringify({ current_page: p, page_size: pageSize }),
        });
        if (seq !== loadSeq.current) return;

        if (data == null) {
          setItems([]);
          setTotal(0);
          return;
        }

        if (data?.error) {
          setError(data.error);
          setItems([]);
          setTotal(0);
          return;
        }
        const list = Array.isArray(data?.items)
          ? data!.items!
          : Array.isArray(data)
            ? (data as unknown as Application[])
            : [];
        setItems(list);
        setTotal(data?.pagination?.number_of_items ?? list.length);
      } catch (e) {
        if (seq !== loadSeq.current) return;
        setError(e instanceof Error ? e.message : "Failed to load");
      } finally {
        if (seq === loadSeq.current) {
          setLoading(false);
          setLoadedOnce(true);
        }
      }
    },
    [execute, pageSize],
  );

  useEffect(() => {
    load(page);
  }, [page, load]);


  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload: Record<string, unknown> = {
        application_mnemonic: form.application_mnemonic.trim(),
        application_description: form.application_description || null,
        application_url: form.application_url || null,
      };
      if (form.order !== "") payload.order = Number(form.order);
      if (form.width !== "") payload.width = Number(form.width);
      if (form.icon_base64) payload.icon_base64 = form.icon_base64;

      const res = await execute("/api/applications/create", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (res?.error) {
        setError(res.error);
        return;
      }
      setModalOpen(false);
      setForm(emptyForm);
      await load(page);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!itemToDelete) return;
    setDeleting(true);
    setError(null);
    try {
      const res = await execute("/api/applications/delete", {
        method: "POST",
        body: JSON.stringify({ id: itemToDelete.id }),
      });
      if (res?.error) {
        setError(res.error);
        toast.error(res.error);
        return;
      }
      setDeleteModalOpen(false);
      setItemToDelete(null);
      await load(page);
      toast.success(t("applicationDeleted"));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Delete failed";
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setDeleting(false);
    }
  }

  function openDeleteModal(item: Application) {
    setItemToDelete(item);
    setDeleteModalOpen(true);
  }

  return (
    <div>
      <div className="flex items-center justify-between gap-4 mb-6">
        <h1 className="font-(--font-heading) text-[24px] text-black">{t("applications")}</h1>
        <Can action="application:create">
          <AddButton onClick={() => setModalOpen(true)} />
        </Can>
      </div>

      {error && <div className="bg-[rgba(192,57,43,0.1)] text-[#c0392b] p-2.5 px-3.5 rounded mb-4">{error}</div>}

      <div className="bg-white rounded-[10px] py-6 shadow-sm">
        {loading || !loadedOnce ? (
          <TableSkeleton rows={pageSize} headers={["Mnemonic", "Description", "URL", "Status", "Actions"]} />
        ) : (
          <Table
            columns={[
              {
                key: "mnemonic",
                header: "Mnemonic",
                render: (app) => app.application_mnemonic,
              },
              {
                key: "description",
                header: "Description",
                render: (app) => app.application_description || "—",
              },
              {
                key: "url",
                header: "URL",
                render: (app) => app.application_url || "—",
              },
              {
                key: "status",
                header: "Status",
                render: (app) => (
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
                render: (app) => (
                  <Can action="application:delete">
                    <button
                      type="button"
                      className="inline-block font-sans text-[16px] font-medium px-3 py-1.5 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-[rgba(192,57,43,0.1)] text-[#c0392b] hover:bg-[rgba(192,57,43,0.2)] disabled:opacity-50 disabled:not-allowed"
                      onClick={(e) => {
                        e.stopPropagation();
                        openDeleteModal(app);
                      }}
                      disabled={app.is_self_registered}
                      title={app.is_self_registered ? "Cannot delete self-registered applications" : "Delete application"}
                    >
                      {t("delete")}
                    </button>
                  </Can>
                ),
              },
            ]}
            data={items}
            onRowClick={(app) => router.push(`/applications/${app.id}`)}
            emptyMessage={t("noData")}
          />
        )}
        {!loading && loadedOnce && (
          <Pagination
            page={page}
            pageSize={pageSize}
            total={total}
            onPageChange={setPage}
          />
        )}
      </div>

      <Modal
        open={modalOpen}
        title="Add Application"
        onClose={() => setModalOpen(false)}
      >
        <form onSubmit={handleCreate}>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5 col-span-full">
              <label htmlFor="mnemonic" className="text-[16px] font-medium text-gray-600">Mnemonic *</label>
              <input
                id="mnemonic"
                required
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={form.application_mnemonic}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    application_mnemonic: e.target.value,
                  }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5 col-span-full">
              <label htmlFor="description" className="text-[16px] font-medium text-gray-600">Description</label>
              <textarea
                id="description"
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] min-h-20 resize-y"
                value={form.application_description}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    application_description: e.target.value,
                  }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5 col-span-full">
              <label htmlFor="url" className="text-[16px] font-medium text-gray-600">URL</label>
              <input
                id="url"
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={form.application_url}
                onChange={(e) =>
                  setForm((f) => ({ ...f, application_url: e.target.value }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="order" className="text-[16px] font-medium text-gray-600">Order</label>
              <input
                id="order"
                type="number"
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={form.order}
                onChange={(e) =>
                  setForm((f) => ({ ...f, order: e.target.value }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="width" className="text-[16px] font-medium text-gray-600">Width</label>
              <input
                id="width"
                type="number"
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={form.width}
                onChange={(e) =>
                  setForm((f) => ({ ...f, width: e.target.value }))
                }
              />
            </div>
            <IconBase64Field
              value={form.icon_base64}
              mimeType={form.icon_mime_type}
              onChange={(base64, mimeType) =>
                setForm((f) => ({
                  ...f,
                  icon_base64: base64,
                  icon_mime_type: mimeType,
                }))
              }
              onClear={() =>
                setForm((f) => ({
                  ...f,
                  icon_base64: "",
                  icon_mime_type: "image/png",
                }))
              }
            />
          </div>
          <div className="flex gap-3 justify-end mt-5">
            <button
              type="button"
              className="inline-block font-sans text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-transparent text-black border border-gray-300 hover:bg-gray-100 disabled:opacity-50 disabled:not-allowed"
              onClick={() => setModalOpen(false)}
            >
              {t("cancel")}
            </button>
            <button type="submit" className="inline-block font-sans text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-[#f5bb1a] text-black hover:bg-[#e0a800] disabled:opacity-50 disabled:not-allowed" disabled={saving}>
              {saving ? t("saving") : t("save")}
            </button>
          </div>
        </form>
      </Modal>

      <ConfirmModal
        open={deleteModalOpen}
        title={t("deleteApplication")}
        warningText={itemToDelete?.is_self_registered ? t("cannotDeleteSelfRegistered") : t("deleteWillRemoveAllData")}
        confirming={deleting}
        onConfirm={handleDelete}
        onCancel={() => {
          setDeleteModalOpen(false);
          setItemToDelete(null);
        }}
      />
    </div>
  );
}
