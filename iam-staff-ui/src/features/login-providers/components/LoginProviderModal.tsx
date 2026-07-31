"use client";

import { useTranslations } from "next-intl";
import {
  Button,
  CheckboxField,
  FormActions,
  IconBase64Field,
  InputField,
  Modal,
  SelectField,
  TextAreaField,
} from "@/components";

const AUTH_METHODS = [
  "client_secret_post",
  "client_secret_basic",
  "private_key_jwt",
  "private_key_jwt_keymanager",
] as const;

interface LoginProviderForm {
  provider_name: string;
  description: string;
  client_id: string;
  client_secret: string;
  client_private_key: string;
  token_endpoint_auth_method: string;
  issuer: string;
  authorization_endpoint: string;
  token_endpoint: string;
  userinfo_endpoint: string;
  server_metadata_url: string;
  jwks_uri: string;
  oauth_callback_url: string;
  default_redirect_uri: string;
  scope: string;
  enable_pkce: boolean;
  adapter_name: string;
  extra_authorize_params: string;
  jwt_assertion_aud: string;
  audiences: string;
  icon_base64: string;
  icon_mime_type: string;
}

interface LoginProviderModalProps {
  onClose: () => void;
  form: LoginProviderForm;
  onChange: (field: keyof LoginProviderForm, value: any) => void;
  onSave: (e: React.FormEvent) => Promise<void>;
  saving: boolean;
}

const emptyForm: LoginProviderForm = {
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

export default function LoginProviderModal({
  onClose,
  form,
  onChange,
  onSave,
  saving,
}: LoginProviderModalProps) {
  const t = useTranslations();

  return (
    <Modal title="Add Login Provider" onClose={onClose} width="800">
      <form onSubmit={onSave}>
        <div className="grid grid-cols-2 gap-4">
          <InputField
            label="Provider name"
            value={form.provider_name}
            onChange={(value) => onChange("provider_name", value)}
            required
          />
          <InputField
            label="Client ID"
            value={form.client_id}
            onChange={(value) => onChange("client_id", value)}
            required
          />
          <TextAreaField
            label="Description"
            value={form.description}
            onChange={(value) => onChange("description", value)}
            className="col-span-full"
            rows={3}
          />
          <InputField
            label="Issuer"
            value={form.issuer}
            onChange={(value) => onChange("issuer", value)}
            required
          />
          <SelectField
            label="Auth method"
            value={form.token_endpoint_auth_method}
            onChange={(value) => onChange("token_endpoint_auth_method", value)}
            options={AUTH_METHODS.map((m) => ({ value: m, label: m }))}
            required
          />
          <InputField
            label="Client secret"
            type="password"
            value={form.client_secret}
            onChange={(value) => onChange("client_secret", value)}
          />
          <TextAreaField
            label="Client private key"
            value={form.client_private_key}
            onChange={(value) => onChange("client_private_key", value)}
            rows={3}
          />
          <InputField
            label="OAuth callback URL"
            value={form.oauth_callback_url}
            onChange={(value) => onChange("oauth_callback_url", value)}
            className="col-span-full"
            required
          />
          <InputField
            label="Server metadata URL"
            value={form.server_metadata_url}
            onChange={(value) => onChange("server_metadata_url", value)}
          />
          <InputField
            label="Default redirect URI"
            value={form.default_redirect_uri}
            onChange={(value) => onChange("default_redirect_uri", value)}
          />
          <InputField
            label="Authorization endpoint"
            value={form.authorization_endpoint}
            onChange={(value) => onChange("authorization_endpoint", value)}
          />
          <InputField
            label="Token endpoint"
            value={form.token_endpoint}
            onChange={(value) => onChange("token_endpoint", value)}
          />
          <InputField
            label="Userinfo endpoint"
            value={form.userinfo_endpoint}
            onChange={(value) => onChange("userinfo_endpoint", value)}
          />
          <InputField
            label="JWKS URI"
            value={form.jwks_uri}
            onChange={(value) => onChange("jwks_uri", value)}
          />
          <InputField
            label="Scope"
            value={form.scope}
            onChange={(value) => onChange("scope", value)}
          />
          <InputField
            label="Adapter name"
            value={form.adapter_name}
            onChange={(value) => onChange("adapter_name", value)}
          />
          <InputField
            label="JWT assertion audience"
            value={form.jwt_assertion_aud}
            onChange={(value) => onChange("jwt_assertion_aud", value)}
          />
          <InputField
            label="Audiences"
            value={form.audiences}
            onChange={(value) => onChange("audiences", value)}
            className="col-span-full"
          />
          <TextAreaField
            label="Extra authorize params"
            value={form.extra_authorize_params}
            onChange={(value) => onChange("extra_authorize_params", value)}
            className="col-span-full"
            rows={3}
          />
          <IconBase64Field
            value={form.icon_base64}
            mimeType={form.icon_mime_type}
            onChange={(base64, mimeType) => {
              onChange("icon_base64", base64);
              onChange("icon_mime_type", mimeType);
            }}
            onClear={() => {
              onChange("icon_base64", "");
              onChange("icon_mime_type", "image/png");
            }}
          />
          <CheckboxField
            label="Enable PKCE"
            checked={form.enable_pkce}
            onChange={(checked) => onChange("enable_pkce", checked)}
          />
        </div>
        <FormActions>
          <Button type="button" variant="secondary" onClick={onClose}>
            {t("cancel")}
          </Button>
          <Button type="submit" variant="primary" disabled={saving}>
            {saving ? t("saving") : t("save")}
          </Button>
        </FormActions>
      </form>
    </Modal>
  );
}

export { emptyForm };
