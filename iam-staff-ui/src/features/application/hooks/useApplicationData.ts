import { useCallback, useRef, useState } from "react";
import { useFetch } from "@/shared/hooks/useFetch";
import { toast } from "react-toastify";
import { Application, ApplicationForm } from "../types";

export function useApplicationData(applicationId: number) {
  const { execute } = useFetch();
  const [app, setApp] = useState<Application | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadedOnce, setLoadedOnce] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<ApplicationForm>({
    application_description: "",
    application_url: "",
    api_url: "",
    order: "",
    width: "",
    icon_base64: "",
    icon_mime_type: "image/png",
  });
  const loadSeq = useRef(0);

  const loadApp = useCallback(async () => {
    const seq = ++loadSeq.current;
    setLoading(true);
    try {
      const data = await execute("/api/applications/get", {
        method: "POST",
        body: JSON.stringify({ id: applicationId }),
      });
      if (seq !== loadSeq.current) return;
      if (data == null) {
        setApp(null);
        return;
      }

      if (data?.error) {
        toast.error(data.error);
        setApp(null);
        return;
      }
      setApp(data);
      setForm({
        application_description: data?.application_description || "",
        application_url: data?.application_url || "",
        api_url: data?.api_url || "",
        order: data?.order != null ? String(data.order) : "",
        width: data?.width != null ? String(data.width) : "",
        icon_base64: data?.icon_base64 || "",
        icon_mime_type: "image/png",
      });
    } catch (e) {
      if (seq !== loadSeq.current) return;
      const errorMessage = e instanceof Error ? e.message : "Failed to load";
      toast.error(errorMessage);
    } finally {
      if (seq === loadSeq.current) {
        setLoading(false);
        setLoadedOnce(true);
      }
    }
  }, [applicationId, execute]);

  const saveApplication = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setSaving(true);
      try {
        const payload: Record<string, unknown> = {
          id: applicationId,
          application_description: form.application_description || null,
          application_url: form.application_url || null,
          api_url: form.api_url || null,
        };
        if (form.order !== "") payload.order = Number(form.order);
        if (form.width !== "") payload.width = Number(form.width);
        const iconBase64 = form.icon_base64 || "";
        payload.icon_base64 = iconBase64.startsWith("data:") ? iconBase64.split(",")[1] : iconBase64;

        const res = await execute("/api/applications/update", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        if (res?.error) {
          toast.error(res.error);
          return;
        }
        setApp(res);
        toast.success("Application updated successfully");
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Save failed";
        toast.error(errorMessage);
      } finally {
        setSaving(false);
      }
    },
    [applicationId, execute, form],
  );

  const reset = useCallback(() => {
    setApp(null);
    setLoading(true);
    setLoadedOnce(false);
    loadSeq.current += 1;
  }, []);

  return {
    app,
    form,
    loading,
    loadedOnce,
    saving,
    loadApp,
    saveApplication,
    setForm,
    reset,
    setAppForm: setForm,
  };
}
