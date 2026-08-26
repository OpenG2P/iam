import { useTranslations } from "next-intl";
import {
  Button,
  Card,
  CheckboxField,
  FormActions,
  IconBase64Field,
  InputField,
  SelectField,
  TextAreaField,
} from "@/components";
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
        <InputField
          label="Provider name"
          value={form.provider_name}
          onChange={(value) => onChange("provider_name", value)}
          disabled={!canEdit || saving}
          required
        />
        <InputField
          label="Client ID"
          value={form.client_id}
          onChange={(value) => onChange("client_id", value)}
          disabled={!canEdit || saving}
          required
        />
        <TextAreaField
          label="Description"
          value={form.description}
          onChange={(value) => onChange("description", value)}
          disabled={!canEdit || saving}
          className="col-span-full"
          rows={1}
        />
        <SelectField
          label="Token endpoint auth method"
          value={form.token_endpoint_auth_method}
          onChange={(value) => onChange("token_endpoint_auth_method", value)}
          options={AUTH_METHODS.map((method) => ({ value: method, label: method }))}
          disabled={!canEdit || saving}
          required
        />
        <InputField
          label="Issuer"
          value={form.issuer}
          onChange={(value) => onChange("issuer", value)}
          disabled={!canEdit || saving}
          required
        />
        <InputField
          label="Authorization endpoint"
          value={form.authorization_endpoint}
          onChange={(value) => onChange("authorization_endpoint", value)}
          disabled={!canEdit || saving}
        />
        <InputField
          label="Token endpoint"
          value={form.token_endpoint}
          onChange={(value) => onChange("token_endpoint", value)}
          disabled={!canEdit || saving}
        />
        <InputField
          label="Userinfo endpoint"
          value={form.userinfo_endpoint}
          onChange={(value) => onChange("userinfo_endpoint", value)}
          disabled={!canEdit || saving}
        />
        <InputField
          label="Server metadata URL"
          value={form.server_metadata_url}
          onChange={(value) => onChange("server_metadata_url", value)}
          disabled={!canEdit || saving}
        />
        <InputField
          label="JWKS URI"
          value={form.jwks_uri}
          onChange={(value) => onChange("jwks_uri", value)}
          disabled={!canEdit || saving}
        />
        <InputField
          label="Adapter name"
          value={form.adapter_name}
          onChange={(value) => onChange("adapter_name", value)}
          disabled={!canEdit || saving}
        />
        <InputField
          label="Scope"
          value={form.scope}
          onChange={(value) => onChange("scope", value)}
          disabled={!canEdit || saving}
        />
        <InputField
          label="Extra authorize params"
          value={form.extra_authorize_params}
          onChange={(value) => onChange("extra_authorize_params", value)}
          disabled={!canEdit || saving}
        />
        <InputField
          label="JWT assertion audience"
          value={form.jwt_assertion_aud}
          onChange={(value) => onChange("jwt_assertion_aud", value)}
          disabled={!canEdit || saving}
        />
        <InputField
          label="Audiences"
          value={form.audiences}
          onChange={(value) => onChange("audiences", value)}
          disabled={!canEdit || saving}
        />
        <InputField
          label="OAuth callback URL"
          value={form.oauth_callback_url}
          onChange={(value) => onChange("oauth_callback_url", value)}
          disabled={!canEdit || saving}
          required
        />
        <InputField
          label="Default redirect URI"
          value={form.default_redirect_uri}
          onChange={(value) => onChange("default_redirect_uri", value)}
          disabled={!canEdit || saving}
        />
        <InputField
          label="Keymanager app ID"
          value={form.keymanager_app_id}
          onChange={(value) => onChange("keymanager_app_id", value)}
          disabled={!canEdit || saving}
        />
        <InputField
          label="Keymanager ref ID"
          value={form.keymanager_ref_id}
          onChange={(value) => onChange("keymanager_ref_id", value)}
          disabled={!canEdit || saving}
        />
        <CheckboxField
          label="Enable PKCE"
          checked={form.enable_pkce}
          onChange={(checked) => onChange("enable_pkce", checked)}
          disabled={!canEdit || saving}
        />
        <div className="flex flex-col gap-1.5 col-span-full">
          <label className="text-[16px] font-medium text-black">Client secret</label>
          <InputField
            type="password"
            placeholder={
              provider?.has_client_secret
                ? "•••••••• (leave blank to keep)"
                : "Not set"
            }
            value={form.client_secret}
            onChange={(value) => onChange("client_secret", value)}
            disabled={!canEdit || saving}
          />
          {provider?.has_client_secret && (
            <span className="inline-block text-[16px] font-medium text-[#27ae60] mt-1">{t("secretConfigured")}</span>
          )}
          <span className="text-[16px] text-gray-500 mt-0.5">
            {t("writeOnlySecretHint")}
          </span>
        </div>
        <div className="flex flex-col gap-1.5 col-span-full">
          <label className="text-[16px] font-medium text-black">Client private key</label>
          <TextAreaField
            placeholder={
              provider?.has_client_private_key
                ? "(leave blank to keep)"
                : "Not set"
            }
            value={form.client_private_key}
            onChange={(value) => onChange("client_private_key", value)}
            disabled={!canEdit || saving}
            rows={2}
            className="font-mono text-sm"
          />
          {provider?.has_client_private_key && (
            <span className="inline-block text-[16px] font-medium text-[#27ae60] mt-1">{t("privateKeyConfigured")}</span>
          )}
          <span className="text-[16px] text-gray-500 mt-0.5">
            {t("writeOnlyKeyHint")}
          </span>
        </div>
        {/* <IconBase64Field
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
        /> */}
      </div>
      {canEdit && (
        <FormActions>
          <Button type="submit" variant="primary" disabled={saving}>
            {saving ? t("saving") : t("save")}
          </Button>
        </FormActions>
      )}
    </form>
  );
}
