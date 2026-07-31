"use client";

import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { useRbac } from "@/context/RbacContext";
import { useLoginProviderData } from "@/features/login-providers/hooks/useLoginProviderData";
import {
  LoginProviderForm,
  LoginProviderPageSkeleton,
  LoginProviderNotFound,
} from "@/features/login-providers/components";
import { toast } from "react-toastify";

export default function LoginProviderDetailPage() {
  const t = useTranslations();
  const { can } = useRbac();
  const params = useParams();
  const providerId = Number(params.id);

  const {
    provider,
    form,
    loading,
    saving,
    error,
    save,
    setForm,
    setError,
  } = useLoginProviderData(providerId);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    const result = await save(form);
    if (result) {
      toast.success(t("loginProviderUpdated"));
    }
  }

  if (loading) {
    return <LoginProviderPageSkeleton />;
  }

  if (!provider) {
    return <LoginProviderNotFound backHref="/login-providers" />;
  }

  return (
    <div>
      <div className="flex items-center justify-between gap-4 mb-6">
        <h1 className="font-(--font-heading) text-[24px] text-black mb-4">{provider.provider_name}</h1>
      </div>

      {error && (
        <div className="bg-[rgba(192,57,43,0.1)] text-[#c0392b] p-3.5 rounded mb-4 text-[16px] font-medium">
          {error}
        </div>
      )}

      <div className="bg-white rounded-[10px] p-6 shadow-[0_1px_2px_rgba(6,19,39,0.05)] border border-gray-100">
        <LoginProviderForm
          form={form}
          provider={provider}
          canEdit={can("loginProvider:edit")}
          saving={saving}
          onChange={(field, value) => setForm((f: any) => ({ ...f, [field]: value }))}
          onSave={handleSave}
        />
      </div>
    </div>
  );
}
