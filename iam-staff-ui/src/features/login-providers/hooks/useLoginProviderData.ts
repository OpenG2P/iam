import { useCallback, useEffect, useRef, useState } from "react";
import { useFetch } from "@/shared/hooks/useFetch";
import { LoginProvider, LoginProviderForm } from "../types";

export function useLoginProviderData(providerId: number) {
  const { execute } = useFetch();
  const [provider, setProvider] = useState<LoginProvider | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const loadSeq = useRef(0);
  const [form, setForm] = useState<LoginProviderForm>({
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

  const save = useCallback(
    async (currentForm: LoginProviderForm) => {
      setSaving(true);
      setError(null);
      try {
        const payload: Record<string, unknown> = {
          id: providerId,
          provider_name: currentForm.provider_name.trim(),
          description: currentForm.description || null,
          client_id: currentForm.client_id.trim(),
          token_endpoint_auth_method: currentForm.token_endpoint_auth_method,
          issuer: currentForm.issuer.trim(),
          authorization_endpoint: currentForm.authorization_endpoint || null,
          token_endpoint: currentForm.token_endpoint || null,
          userinfo_endpoint: currentForm.userinfo_endpoint || null,
          server_metadata_url: currentForm.server_metadata_url || null,
          jwks_uri: currentForm.jwks_uri || null,
          adapter_name: currentForm.adapter_name || null,
          scope: currentForm.scope || null,
          enable_pkce: currentForm.enable_pkce,
          extra_authorize_params: currentForm.extra_authorize_params || null,
          jwt_assertion_aud: currentForm.jwt_assertion_aud || null,
          audiences: currentForm.audiences || null,
          oauth_callback_url: currentForm.oauth_callback_url.trim(),
          default_redirect_uri: currentForm.default_redirect_uri || null,
          keymanager_app_id: currentForm.keymanager_app_id || null,
          keymanager_ref_id: currentForm.keymanager_ref_id || null,
        };
        payload.icon_base64 = currentForm.icon_base64 || "";
        // Write-only secrets: only send when user entered a new value
        if (currentForm.client_secret.trim()) {
          payload.client_secret = currentForm.client_secret;
        }
        if (currentForm.client_private_key.trim()) {
          payload.client_private_key = currentForm.client_private_key;
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
        return res;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Save failed");
        return null;
      } finally {
        setSaving(false);
      }
    },
    [providerId, execute],
  );

  useEffect(() => {
    load();
  }, [providerId]);

  const reset = useCallback(() => {
    setProvider(null);
    setLoading(true);
    setError(null);
    loadSeq.current += 1;
  }, []);

  return {
    provider,
    form,
    loading,
    saving,
    error,
    load,
    save,
    setForm,
    setError,
    reset,
  };
}
