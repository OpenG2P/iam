"use client";

import { useTranslations } from "next-intl";
import Image from "next/image";
import BackLink from "@/components/BackLink";

interface LoginProviderNotFoundProps {
  backHref: string;
}

export default function LoginProviderNotFound({ backHref }: LoginProviderNotFoundProps) {
  const t = useTranslations();

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
      <BackLink href={backHref} />
    </div>
  );
}
