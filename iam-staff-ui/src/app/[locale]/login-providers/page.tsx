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

const AUTH_METHODS = [
  "client_secret_post",
  "client_secret_basic",
  "private_key_jwt",
  "private_key_jwt_keymanager",
] as const;

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

const emptyForm = {
  provider_name: "",
  description: "",
  client_id: "",
  client_secret: "",
  client_private_key: "",
  token_endpoint_auth_method: "client_secret_post",
  issuer: "",
  authorization_endpoint: "",
  token_endpoint: "",
  userinfo_endpoint: "",
  server_metadata_url: "",
  jwks_uri: "",
  oauth_callback_url: "",
  default_redirect_uri: "",
  scope: "openid profile email",
  enable_pkce: false,
  adapter_name: "",
  extra_authorize_params: "",
  jwt_assertion_aud: "",
  audiences: "",
  icon_base64: "",
  icon_mime_type: "image/png",
};

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
  }, [page, load]);


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
        <h1 className="font-(--font-heading) text-[24px] text-black">{t("loginProviders")}</h1>
        <Can action="loginProvider:create">
          <AddButton onClick={() => setModalOpen(true)} />
        </Can>
      </div>

      {error && <div className="bg-[rgba(192,57,43,0.1)] text-[#c0392b] p-2.5 px-3.5 rounded mb-4">{error}</div>}

      <div className="bg-white rounded-[10px] py-6 shadow-sm">
        {loading || !loadedOnce ? (
          <TableSkeleton rows={pageSize} headers={["Name", "Client ID", "Issuer", "Auth Method", "Status", "Actions"]} />
        ) : (
          <Table
            columns={[
              {
                key: "name",
                header: "Name",
                render: (lp) => lp.provider_name,
              },
              {
                key: "clientId",
                header: "Client ID",
                render: (lp) => lp.client_id,
              },
              {
                key: "issuer",
                header: "Issuer",
                render: (lp) => lp.issuer,
              },
              {
                key: "authMethod",
                header: "Auth Method",
                render: (lp) => lp.token_endpoint_auth_method || "—",
              },
              {
                key: "status",
                header: "Status",
                render: (lp) => (
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
                render: (lp) => (
                  <Can action="loginProvider:delete">
                    <button
                      type="button"
                      className="inline-block font-sans text-[16px] font-medium px-3 py-1.5 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-[rgba(192,57,43,0.1)] text-[#c0392b] hover:bg-[rgba(192,57,43,0.2)] disabled:opacity-50 disabled:not-allowed"
                      onClick={(e) => {
                        e.stopPropagation();
                        openDeleteModal(lp);
                      }}
                      title="Delete login provider"
                    >
                      {t("delete")}
                    </button>
                  </Can>
                ),
              },
            ]}
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

      <Modal
        open={modalOpen}
        title="Add Login Provider"
        onClose={() => setModalOpen(false)}
        wide
      >
        <form onSubmit={handleCreate}>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Provider name *</label>
              <input
                required
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={form.provider_name}
                onChange={(e) =>
                  setForm((f) => ({ ...f, provider_name: e.target.value }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Client ID *</label>
              <input
                required
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={form.client_id}
                onChange={(e) =>
                  setForm((f) => ({ ...f, client_id: e.target.value }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5 col-span-full">
              <label className="text-[16px] font-medium text-gray-600">Description</label>
              <textarea
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] min-h-20 resize-y"
                value={form.description}
                onChange={(e) =>
                  setForm((f) => ({ ...f, description: e.target.value }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Issuer *</label>
              <input
                required
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={form.issuer}
                onChange={(e) =>
                  setForm((f) => ({ ...f, issuer: e.target.value }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Auth method *</label>
              <select
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={form.token_endpoint_auth_method}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    token_endpoint_auth_method: e.target.value,
                  }))
                }
              >
                {AUTH_METHODS.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Client secret</label>
              <input
                type="password"
                autoComplete="new-password"
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={form.client_secret}
                onChange={(e) =>
                  setForm((f) => ({ ...f, client_secret: e.target.value }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Client private key</label>
              <textarea
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] min-h-20 resize-y"
                value={form.client_private_key}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    client_private_key: e.target.value,
                  }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5 col-span-full">
              <label className="text-[16px] font-medium text-gray-600">OAuth callback URL *</label>
              <input
                required
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={form.oauth_callback_url}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    oauth_callback_url: e.target.value,
                  }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Server metadata URL</label>
              <input
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={form.server_metadata_url}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    server_metadata_url: e.target.value,
                  }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Default redirect URI</label>
              <input
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={form.default_redirect_uri}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    default_redirect_uri: e.target.value,
                  }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Authorization endpoint</label>
              <input
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={form.authorization_endpoint}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    authorization_endpoint: e.target.value,
                  }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Token endpoint</label>
              <input
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={form.token_endpoint}
                onChange={(e) =>
                  setForm((f) => ({ ...f, token_endpoint: e.target.value }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Userinfo endpoint</label>
              <input
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={form.userinfo_endpoint}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    userinfo_endpoint: e.target.value,
                  }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">JWKS URI</label>
              <input
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={form.jwks_uri}
                onChange={(e) =>
                  setForm((f) => ({ ...f, jwks_uri: e.target.value }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Scope</label>
              <input
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={form.scope}
                onChange={(e) =>
                  setForm((f) => ({ ...f, scope: e.target.value }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Adapter name</label>
              <input
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={form.adapter_name}
                onChange={(e) =>
                  setForm((f) => ({ ...f, adapter_name: e.target.value }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">JWT assertion audience</label>
              <input
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={form.jwt_assertion_aud}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    jwt_assertion_aud: e.target.value,
                  }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5 col-span-full">
              <label className="text-[16px] font-medium text-gray-600">Audiences</label>
              <input
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                value={form.audiences}
                onChange={(e) =>
                  setForm((f) => ({ ...f, audiences: e.target.value }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5 col-span-full">
              <label className="text-[16px] font-medium text-gray-600">Extra authorize params</label>
              <textarea
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] min-h-20 resize-y"
                value={form.extra_authorize_params}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    extra_authorize_params: e.target.value,
                  }))
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
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">
                <input
                  type="checkbox"
                  checked={form.enable_pkce}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, enable_pkce: e.target.checked }))
                  }
                />{" "}
                Enable PKCE
              </label>
            </div>
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
        title={t("deleteLoginProvider")}
        warningText={t("deleteWillRemoveAllData")}
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
