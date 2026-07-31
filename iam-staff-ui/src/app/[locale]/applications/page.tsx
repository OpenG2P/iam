"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import { useRouter } from "@/i18n/navigation";
import { useFetch } from "@/shared/hooks/useFetch";
import { toast } from "react-toastify";
import {
  AddButton,
  Can,
  ConfirmModal,
  ErrorAlert,
  Pagination,
  Table,
  TableSkeleton,
} from "@/components";
import { ApplicationModal, emptyApplicationForm } from "@/features/application/components";
import { getApplicationColumns } from "@/features/application/utils/applicationTableColumns";
import { useConfig } from "@/context/ConfigContext";

const emptyForm = emptyApplicationForm;

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
  }, [page]);


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

      {error && <ErrorAlert>{error}</ErrorAlert>}

      <div className="bg-white rounded-[10px] py-6 shadow-sm">
        {loading || !loadedOnce ? (
          <TableSkeleton rows={pageSize} headers={["Mnemonic", "Description", "URL", "Status", "Actions"]} />
        ) : (
          <Table
            columns={getApplicationColumns({ onDelete: openDeleteModal, t })}
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

      {modalOpen && (
        <ApplicationModal
          onClose={() => setModalOpen(false)}
          form={form}
          onChange={(field, value) => setForm((f) => ({ ...f, [field]: value }))}
          onSave={handleCreate}
          saving={saving}
        />
      )}

      {deleteModalOpen && (
        <ConfirmModal
          title={t("deleteApplication")}
          warningText={itemToDelete?.is_self_registered ? t("cannotDeleteSelfRegistered") : t("deleteWillRemoveAllData")}
          confirming={deleting}
          onConfirm={handleDelete}
          onCancel={() => {
            setDeleteModalOpen(false);
            setItemToDelete(null);
          }}
        />
      )}
    </div>
  );
}
