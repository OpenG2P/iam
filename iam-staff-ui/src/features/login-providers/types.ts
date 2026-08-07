export interface LoginProvider {
  id: number;
  provider_name: string;
  description?: string | null;
  icon_base64?: string | null;
  icon_mime_type?: string | null;
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

export interface LoginProviderForm {
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
  adapter_name: string;
  scope: string;
  enable_pkce: boolean;
  extra_authorize_params: string;
  jwt_assertion_aud: string;
  audiences: string;
  oauth_callback_url: string;
  default_redirect_uri: string;
  keymanager_app_id: string;
  keymanager_ref_id: string;
  icon_base64: string;
  icon_mime_type: string;
}

export const AUTH_METHODS = [
  "client_secret_post",
  "client_secret_basic",
  "private_key_jwt",
  "private_key_jwt_keymanager",
] as const;
