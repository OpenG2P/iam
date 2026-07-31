"use client";

import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import Image from "next/image";
import BackLink from "@/components/BackLink";
import { useRbac } from "@/context/RbacContext";
import { useLoginProviderData } from "@/features/login-providers/hooks/useLoginProviderData";
import LoginProviderForm from "@/features/login-providers/components/LoginProviderForm";
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
          alt={t("loginProviderNotFoundIllustration")}
          className="mb-6"
          priority
        />
        <h1 className="mb-2 text-4xl font-bold text-gray-900">
          {t("error404Title")}
        </h1>
        <p className="mb-8 text-lg text-gray-600 max-w-md text-center">
          {t("error404Subtitle")}
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
