"use client";

import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import Image from "next/image";
import { useFetch } from "@/shared/hooks/useFetch";
import BackLink from "@/components/BackLink";
import Can from "@/components/Can";
import IconBase64Field from "@/components/IconBase64Field";
import { useRbac } from "@/context/RbacContext";

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
  icon_base64?: string | null;
  client_id: string;
  has_client_secret?: boolean;
  has_client_private_key?: boolean;
  token_endpoint_auth_method: string;
  issuer: string;
  authorization_endpoint?: string | null;
  token_endpoint?: string | null;
  userinfo_endpoint?: string | null;
  server_metadata_url?: string | null;
  jwks_uri?: string | null;
  adapter_name?: string | null;
  scope?: string | null;
  enable_pkce?: boolean | null;
  extra_authorize_params?: string | null;
  jwt_assertion_aud?: string | null;
  audiences?: string | null;
  oauth_callback_url: string;
  default_redirect_uri?: string | null;
  keymanager_app_id?: string | null;
  keymanager_ref_id?: string | null;
  active?: boolean;
}

export default function LoginProviderDetailPage() {
  const t = useTranslations();
  const { can } = useRbac();
  const params = useParams();
  const providerId = Number(params.id);
  const { execute } = useFetch();

  const [provider, setProvider] = useState<LoginProvider | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const loadSeq = useRef(0);
  const [form, setForm] = useState({
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
    adapter_name: "",
    scope: "",
    enable_pkce: false,
    extra_authorize_params: "",
    jwt_assertion_aud: "",
    audiences: "",
    oauth_callback_url: "",
    default_redirect_uri: "",
    keymanager_app_id: "",
    keymanager_ref_id: "",
    icon_base64: "",
    icon_mime_type: "image/png",
  });

  const load = useCallback(async () => {
    const seq = ++loadSeq.current;
    setLoading(true);
    setError(null);
    try {
      const data = await execute("/api/login-providers/get", {
        method: "POST",
        body: JSON.stringify({ id: providerId }),
      });
      if (seq !== loadSeq.current) return;
      if (data == null) {
        setProvider(null);
        return;
      }

      if (data?.error) {
        setError(data.error);
        setProvider(null);
        return;
      }
      setProvider(data);
      setForm({
        provider_name: data?.provider_name || "",
        description: data?.description || "",
        client_id: data?.client_id || "",
        client_secret: "",
        client_private_key: "",
        token_endpoint_auth_method:
          data?.token_endpoint_auth_method || "client_secret_post",
        issuer: data?.issuer || "",
        authorization_endpoint: data?.authorization_endpoint || "",
        token_endpoint: data?.token_endpoint || "",
        userinfo_endpoint: data?.userinfo_endpoint || "",
        server_metadata_url: data?.server_metadata_url || "",
        jwks_uri: data?.jwks_uri || "",
        adapter_name: data?.adapter_name || "",
        scope: data?.scope || "",
        enable_pkce: !!data?.enable_pkce,
        extra_authorize_params: data?.extra_authorize_params || "",
        jwt_assertion_aud: data?.jwt_assertion_aud || "",
        audiences: data?.audiences || "",
        oauth_callback_url: data?.oauth_callback_url || "",
        default_redirect_uri: data?.default_redirect_uri || "",
        keymanager_app_id: data?.keymanager_app_id || "",
        keymanager_ref_id: data?.keymanager_ref_id || "",
        icon_base64: data?.icon_base64 || "",
        icon_mime_type: "image/png",
      });
    } catch (e) {
      if (seq !== loadSeq.current) return;
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      if (seq === loadSeq.current) {
        setLoading(false);
      }
    }
  }, [providerId, execute]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload: Record<string, unknown> = {
        id: providerId,
        provider_name: form.provider_name.trim(),
        description: form.description || null,
        client_id: form.client_id.trim(),
        token_endpoint_auth_method: form.token_endpoint_auth_method,
        issuer: form.issuer.trim(),
        authorization_endpoint: form.authorization_endpoint || null,
        token_endpoint: form.token_endpoint || null,
        userinfo_endpoint: form.userinfo_endpoint || null,
        server_metadata_url: form.server_metadata_url || null,
        jwks_uri: form.jwks_uri || null,
        adapter_name: form.adapter_name || null,
        scope: form.scope || null,
        enable_pkce: form.enable_pkce,
        extra_authorize_params: form.extra_authorize_params || null,
        jwt_assertion_aud: form.jwt_assertion_aud || null,
        audiences: form.audiences || null,
        oauth_callback_url: form.oauth_callback_url.trim(),
        default_redirect_uri: form.default_redirect_uri || null,
        keymanager_app_id: form.keymanager_app_id || null,
        keymanager_ref_id: form.keymanager_ref_id || null,
      };
      payload.icon_base64 = form.icon_base64 || "";
      // Write-only secrets: only send when user entered a new value
      if (form.client_secret.trim()) {
        payload.client_secret = form.client_secret;
      }
      if (form.client_private_key.trim()) {
        payload.client_private_key = form.client_private_key;
      }

      const res = await execute("/api/login-providers/update", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (res?.error) {
        setError(res.error);
        return;
      }
      setProvider(res);
      setForm((f) => ({ ...f, client_secret: "", client_private_key: "" }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div>
        <BackLink href="/login-providers" />
        <div className="flex items-center justify-between gap-4 mb-6">
          <div className="animate-pulse bg-gray-200 w-[220px] h-[28px] rounded-[8px]" />
        </div>
        <div className="bg-white rounded-[10px] p-6 shadow-[0_1px_2px_rgba(6,19,39,0.05)]">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Array.from({ length: 12 }).map((_, i) => (
              <div key={i} className="flex flex-col gap-1.5">
                <div className="animate-pulse bg-gray-200 w-[80px] h-[12px] mb-2 rounded-[4px]" />
                <div className="animate-pulse bg-gray-200 w-full h-[38px] rounded-[8px]" />
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!provider) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] py-12">
        <Image
          src="/error.png"
          width={200}
          height={200}
          alt="Login provider not found illustration"
          className="mb-6"
          priority
        />

        <h1 className="mb-2 text-4xl font-bold text-gray-900">
          Page Not Found
        </h1>

        <p className="mb-8 text-lg text-gray-600 max-w-md text-center">
          The page you are looking for does not exist.
        </p>

        <BackLink href="/login-providers" />
      </div>
    );
  }

  return (
    <div>
      <BackLink href="/login-providers" />
      <div className="flex items-center justify-between gap-4 mb-6">
        <h1 className="font-[var(--font-heading)] text-[24px] font-bold text-[var(--color-black)] mb-4">{provider.provider_name}</h1>
      </div>

      {error && (
        <div className="bg-[rgba(192,57,43,0.1)] text-[#c0392b] p-3.5 rounded mb-4 text-[16px] font-medium">
          {error}
        </div>
      )}

      <div className="bg-white rounded-[10px] p-6 shadow-[0_1px_2px_rgba(6,19,39,0.05)] border border-gray-100">
        <form onSubmit={handleSave}>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Provider name *</label>
              <input
                required
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                value={form.provider_name}
                disabled={!can("loginProvider:edit") || saving}
                onChange={(e) =>
                  setForm((f) => ({ ...f, provider_name: e.target.value }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Client ID *</label>
              <input
                required
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                value={form.client_id}
                disabled={!can("loginProvider:edit") || saving}
                onChange={(e) =>
                  setForm((f) => ({ ...f, client_id: e.target.value }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5 col-span-full">
              <label className="text-[16px] font-medium text-gray-600">Description</label>
              <textarea
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] min-h-[80px] resize-y disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                value={form.description}
                disabled={!can("loginProvider:edit") || saving}
                onChange={(e) =>
                  setForm((f) => ({ ...f, description: e.target.value }))
                }
              />
            </div>
            <IconBase64Field
              value={form.icon_base64}
              mimeType={form.icon_mime_type}
              disabled={!can("loginProvider:edit") || saving}
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
              <label className="text-[16px] font-medium text-gray-600">Issuer *</label>
              <input
                required
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                value={form.issuer}
                disabled={!can("loginProvider:edit") || saving}
                onChange={(e) =>
                  setForm((f) => ({ ...f, issuer: e.target.value }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Auth method *</label>
              <select
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                value={form.token_endpoint_auth_method}
                disabled={!can("loginProvider:edit") || saving}
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
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                placeholder={
                  provider.has_client_secret
                    ? "•••••••• (leave blank to keep)"
                    : "Not set"
                }
                value={form.client_secret}
                disabled={!can("loginProvider:edit") || saving}
                onChange={(e) =>
                  setForm((f) => ({ ...f, client_secret: e.target.value }))
                }
              />
              {provider.has_client_secret && (
                <span className="inline-block text-[16px] font-medium text-[#27ae60] mt-1">Secret is configured</span>
              )}
              <span className="text-[16px] text-gray-400 mt-0.5">
                Write-only — leave empty to keep the existing secret.
              </span>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Client private key</label>
              <textarea
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] min-h-[80px] resize-y disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                placeholder={
                  provider.has_client_private_key
                    ? "(leave blank to keep)"
                    : "Not set"
                }
                value={form.client_private_key}
                disabled={!can("loginProvider:edit") || saving}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    client_private_key: e.target.value,
                  }))
                }
              />
              {provider.has_client_private_key && (
                <span className="inline-block text-[16px] font-medium text-[#27ae60] mt-1">Private key is configured</span>
              )}
              <span className="text-[16px] text-gray-400 mt-0.5">
                Write-only — leave empty to keep the existing key.
              </span>
            </div>
            <div className="flex flex-col gap-1.5 col-span-full">
              <label className="text-[16px] font-medium text-gray-600">OAuth callback URL *</label>
              <input
                required
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                value={form.oauth_callback_url}
                disabled={!can("loginProvider:edit") || saving}
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
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                value={form.server_metadata_url}
                disabled={!can("loginProvider:edit") || saving}
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
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                value={form.default_redirect_uri}
                disabled={!can("loginProvider:edit") || saving}
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
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                value={form.authorization_endpoint}
                disabled={!can("loginProvider:edit") || saving}
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
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                value={form.token_endpoint}
                disabled={!can("loginProvider:edit") || saving}
                onChange={(e) =>
                  setForm((f) => ({ ...f, token_endpoint: e.target.value }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Userinfo endpoint</label>
              <input
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                value={form.userinfo_endpoint}
                disabled={!can("loginProvider:edit") || saving}
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
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                value={form.jwks_uri}
                disabled={!can("loginProvider:edit") || saving}
                onChange={(e) =>
                  setForm((f) => ({ ...f, jwks_uri: e.target.value }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Scope</label>
              <input
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                value={form.scope}
                disabled={!can("loginProvider:edit") || saving}
                onChange={(e) =>
                  setForm((f) => ({ ...f, scope: e.target.value }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Adapter name</label>
              <input
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                value={form.adapter_name}
                disabled={!can("loginProvider:edit") || saving}
                onChange={(e) =>
                  setForm((f) => ({ ...f, adapter_name: e.target.value }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">JWT assertion audience</label>
              <input
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                value={form.jwt_assertion_aud}
                disabled={!can("loginProvider:edit") || saving}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    jwt_assertion_aud: e.target.value,
                  }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Audiences</label>
              <input
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                value={form.audiences}
                disabled={!can("loginProvider:edit") || saving}
                onChange={(e) =>
                  setForm((f) => ({ ...f, audiences: e.target.value }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Keymanager app ID</label>
              <input
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                value={form.keymanager_app_id}
                disabled={!can("loginProvider:edit") || saving}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    keymanager_app_id: e.target.value,
                  }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-[16px] font-medium text-gray-600">Keymanager ref ID</label>
              <input
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                value={form.keymanager_ref_id}
                disabled={!can("loginProvider:edit") || saving}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    keymanager_ref_id: e.target.value,
                  }))
                }
              />
            </div>
            <div className="flex flex-col gap-1.5 col-span-full">
              <label className="text-[16px] font-medium text-gray-600">Extra authorize params</label>
              <textarea
                className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] min-h-[80px] resize-y disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
                value={form.extra_authorize_params}
                disabled={!can("loginProvider:edit") || saving}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    extra_authorize_params: e.target.value,
                  }))
                }
              />
            </div>
            <div className="flex items-center gap-2 col-span-full mt-2">
              <input
                type="checkbox"
                id="enable_pkce"
                className="w-4 h-4 rounded text-[#f5bb1a] focus:ring-[#f5bb1a]"
                checked={form.enable_pkce}
                disabled={!can("loginProvider:edit") || saving}
                onChange={(e) =>
                  setForm((f) => ({ ...f, enable_pkce: e.target.checked }))
                }
              />
              <label htmlFor="enable_pkce" className="text-[16px] font-medium text-gray-600 select-none">
                Enable PKCE
              </label>
            </div>
          </div>
          <Can action="loginProvider:edit">
            <div className="flex gap-3 justify-end mt-5 pt-4 border-t border-gray-100">
              <button
                type="submit"
                className="inline-block font-sans text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-[#f5bb1a] text-black hover:bg-[#e0a800] disabled:opacity-50 disabled:not-allowed"
                disabled={saving}
              >
                {saving ? t("saving") : t("save")}
              </button>
            </div>
          </Can>
        </form>
      </div>
    </div>
  );
}
