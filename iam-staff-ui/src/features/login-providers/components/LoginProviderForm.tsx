import { useTranslations } from "next-intl";
import IconBase64Field from "@/components/IconBase64Field";
import type { LoginProviderForm } from "../types";
import type { LoginProvider } from "../types";
import { AUTH_METHODS } from "../types";

interface LoginProviderFormProps {
  form: LoginProviderForm;
  provider: LoginProvider | null;
  canEdit: boolean;
  saving: boolean;
  onChange: (field: keyof LoginProviderForm, value: any) => void;
  onSave: (e: React.FormEvent) => Promise<void>;
}

export default function LoginProviderForm({
  form,
  provider,
  canEdit,
  saving,
  onChange,
  onSave,
}: LoginProviderFormProps) {
  const t = useTranslations();

  return (
    <form onSubmit={onSave}>
      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col gap-1.5">
          <label className="text-[16px] font-medium text-gray-600">Provider name *</label>
          <input
            required
            className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            value={form.provider_name}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("provider_name", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[16px] font-medium text-gray-600">Client ID *</label>
          <input
            required
            className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            value={form.client_id}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("client_id", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5 col-span-full">
          <label className="text-[16px] font-medium text-gray-600">Description</label>
          <textarea
            className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] min-h-[80px] resize-y disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            value={form.description}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("description", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[16px] font-medium text-gray-600">Token endpoint auth method *</label>
          <select
            required
            className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            value={form.token_endpoint_auth_method}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("token_endpoint_auth_method", e.target.value)}
          >
            {AUTH_METHODS.map((method) => (
              <option key={method} value={method}>
                {method}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[16px] font-medium text-gray-600">Issuer *</label>
          <input
            required
            className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            value={form.issuer}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("issuer", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[16px] font-medium text-gray-600">Authorization endpoint</label>
          <input
            className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            value={form.authorization_endpoint}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("authorization_endpoint", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[16px] font-medium text-gray-600">Token endpoint</label>
          <input
            className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            value={form.token_endpoint}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("token_endpoint", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[16px] font-medium text-gray-600">Userinfo endpoint</label>
          <input
            className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            value={form.userinfo_endpoint}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("userinfo_endpoint", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[16px] font-medium text-gray-600">Server metadata URL</label>
          <input
            className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            value={form.server_metadata_url}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("server_metadata_url", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[16px] font-medium text-gray-600">JWKS URI</label>
          <input
            className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            value={form.jwks_uri}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("jwks_uri", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[16px] font-medium text-gray-600">Adapter name</label>
          <input
            className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            value={form.adapter_name}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("adapter_name", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[16px] font-medium text-gray-600">Scope</label>
          <input
            className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            value={form.scope}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("scope", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5 items-center">
          <label className="text-[16px] font-medium text-gray-600">Enable PKCE</label>
          <input
            type="checkbox"
            className="w-5 h-5"
            checked={form.enable_pkce}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("enable_pkce", e.target.checked)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[16px] font-medium text-gray-600">Extra authorize params</label>
          <input
            className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            value={form.extra_authorize_params}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("extra_authorize_params", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[16px] font-medium text-gray-600">JWT assertion audience</label>
          <input
            className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            value={form.jwt_assertion_aud}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("jwt_assertion_aud", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[16px] font-medium text-gray-600">Audiences</label>
          <input
            className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            value={form.audiences}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("audiences", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[16px] font-medium text-gray-600">OAuth callback URL *</label>
          <input
            required
            className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            value={form.oauth_callback_url}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("oauth_callback_url", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[16px] font-medium text-gray-600">Default redirect URI</label>
          <input
            className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            value={form.default_redirect_uri}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("default_redirect_uri", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[16px] font-medium text-gray-600">Keymanager app ID</label>
          <input
            className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            value={form.keymanager_app_id}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("keymanager_app_id", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-[16px] font-medium text-gray-600">Keymanager ref ID</label>
          <input
            className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            value={form.keymanager_ref_id}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("keymanager_ref_id", e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1.5 col-span-full">
          <label className="text-[16px] font-medium text-gray-600">Client secret</label>
          <input
            type="password"
            autoComplete="new-password"
            className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
            placeholder={
              provider?.has_client_secret
                ? "•••••••• (leave blank to keep)"
                : "Not set"
            }
            value={form.client_secret}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("client_secret", e.target.value)}
          />
          {provider?.has_client_secret && (
            <span className="inline-block text-[16px] font-medium text-[#27ae60] mt-1">{t("secretConfigured")}</span>
          )}
          <span className="text-[16px] text-gray-400 mt-0.5">
            {t("writeOnlySecretHint")}
          </span>
        </div>
        <div className="flex flex-col gap-1.5 col-span-full">
          <label className="text-[16px] font-medium text-gray-600">Client private key</label>
          <textarea
            className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] min-h-[120px] resize-y disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed font-mono text-sm"
            placeholder={
              provider?.has_client_private_key
                ? "(leave blank to keep)"
                : "Not set"
            }
            value={form.client_private_key}
            disabled={!canEdit || saving}
            onChange={(e) => onChange("client_private_key", e.target.value)}
          />
          {provider?.has_client_private_key && (
            <span className="inline-block text-[16px] font-medium text-[#27ae60] mt-1">{t("privateKeyConfigured")}</span>
          )}
          <span className="text-[16px] text-gray-400 mt-0.5">
            {t("writeOnlyKeyHint")}
          </span>
        </div>
        <IconBase64Field
          value={form.icon_base64}
          mimeType={form.icon_mime_type}
          disabled={!canEdit || saving}
          onChange={(base64, mimeType) => {
            onChange("icon_base64", base64);
            onChange("icon_mime_type", mimeType);
          }}
          onClear={() => {
            onChange("icon_base64", "");
            onChange("icon_mime_type", "image/png");
          }}
        />
      </div>
      {canEdit && (
        <div className="flex gap-3 justify-end mt-5 pt-4 border-t border-gray-100">
          <button
            type="submit"
            className="inline-block font-sans text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-[#f5bb1a] text-black hover:bg-[#e0a800] disabled:opacity-50 disabled:not-allowed"
            disabled={saving}
          >
            {saving ? t("saving") : t("save")}
          </button>
        </div>
      )}
    </form>
  );
}
