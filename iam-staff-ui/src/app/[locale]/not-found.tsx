"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import Image from "next/image";

export default function NotFound() {
  const router = useRouter();
  const t = useTranslations();

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] py-12">
      <Image
        src="/404.png"
        width={200}
        height={200}
        alt="404 error illustration"
        className="mb-6"
        priority
      />

      <h1 className="mb-2 text-4xl font-bold text-gray-900">
        Page Not Found
      </h1>

      <p className="mb-8 text-lg text-gray-600 max-w-md text-center">
        The page you are looking for does not exist.
      </p>

      <button
        onClick={() => router.back()}
        className="flex items-center gap-3 rounded-full bg-gray-900 px-6 py-2.5 text-[16px] font-semibold text-white hover:bg-gray-800 transition-colors"
      >
        <Image
          src="/left_white_arrow.png"
          width={16}
          height={14}
          alt="left arrow"
          priority
        />
        {t("goBack")}
      </button>
    </div>
  );
}
