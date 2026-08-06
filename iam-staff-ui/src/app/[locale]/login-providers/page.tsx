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
import { LoginProviderModal, emptyLoginProviderForm } from "@/features/login-providers/components";
import { getLoginProviderColumns } from "@/features/login-providers/utils/loginProviderTableColumns";
import { useConfig } from "@/context/ConfigContext";

const AUTH_METHODS = [
  "client_secret_post",
  "client_secret_basic",
  "private_key_jwt",
  "private_key_jwt_keymanager",
] as const;

const emptyForm = emptyLoginProviderForm;

interface LoginProvider {
  id: number;
  provider_name: string;
  description?: string | null;
  client_id: string;
  issuer: string;
  active?: boolean;
  token_endpoint_auth_method?: string;
}

interface ListResponse {
  items?: LoginProvider[];
  pagination?: { number_of_items?: number };
  error?: string;
}

export default function LoginProvidersPage() {
  const t = useTranslations();
  const { pageSize } = useConfig();
  const router = useRouter();
  const { execute } = useFetch<ListResponse>();
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<LoginProvider[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadedOnce, setLoadedOnce] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<LoginProvider | null>(null);
  const [deleting, setDeleting] = useState(false);
  const loadSeq = useRef(0);

  const load = useCallback(
    async (p: number) => {
      const seq = ++loadSeq.current;
      setLoading(true);
      setError(null);
      try {
        const data = await execute("/api/login-providers", {
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
            ? (data as unknown as LoginProvider[])
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
        provider_name: form.provider_name.trim(),
        description: form.description || null,
        client_id: form.client_id.trim(),
        token_endpoint_auth_method: form.token_endpoint_auth_method,
        issuer: form.issuer.trim(),
        oauth_callback_url: form.oauth_callback_url.trim(),
        authorization_endpoint: form.authorization_endpoint || null,
        token_endpoint: form.token_endpoint || null,
        userinfo_endpoint: form.userinfo_endpoint || null,
        server_metadata_url: form.server_metadata_url || null,
        jwks_uri: form.jwks_uri || null,
        default_redirect_uri: form.default_redirect_uri || null,
        scope: form.scope || null,
        enable_pkce: form.enable_pkce,
        adapter_name: form.adapter_name || null,
        extra_authorize_params: form.extra_authorize_params || null,
        jwt_assertion_aud: form.jwt_assertion_aud || null,
        audiences: form.audiences || null,
      };
      if (form.icon_base64) payload.icon_base64 = form.icon_base64;
      if (form.client_secret) payload.client_secret = form.client_secret;
      if (form.client_private_key)
        payload.client_private_key = form.client_private_key;

      const res = await execute("/api/login-providers/create", {
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
      const res = await execute("/api/login-providers/delete", {
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
      toast.success(t("loginProviderDeleted"));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Delete failed";
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setDeleting(false);
    }
  }

  function openDeleteModal(item: LoginProvider) {
    setItemToDelete(item);
    setDeleteModalOpen(true);
  }

  return (
    <div>
      <div className="flex items-center justify-between gap-4 mb-6">
        <h1 className="font-semibold text-[24px] text-black">{t("loginProviders")}</h1>
        <Can action="loginProvider:create">
          <AddButton onClick={() => setModalOpen(true)} />
        </Can>
      </div>

      {error && <ErrorAlert>{error}</ErrorAlert>}

      <div className="bg-white rounded-[10px] py-6 shadow-sm">
        {loading || !loadedOnce ? (
          <TableSkeleton rows={pageSize} headers={["Name", "Client ID", "Issuer", "Auth Method", "Status", "Actions"]} />
        ) : (
          <Table
          columns={getLoginProviderColumns({ onDelete: openDeleteModal, t })}
          data={items}
          onRowClick={(lp) => router.push(`/login-providers/${lp.id}`)}
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
        <LoginProviderModal
          onClose={() => setModalOpen(false)}
          form={form}
          onChange={(field, value) => setForm((f) => ({ ...f, [field]: value }))}
          onSave={handleCreate}
          saving={saving}
        />
      )}

      {deleteModalOpen && (
        <ConfirmModal
          title={t("deleteLoginProvider")}
          warningText={t("deleteWillRemoveAllData")}
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
