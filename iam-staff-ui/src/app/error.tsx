"use client";

import { useEffect } from "react";
import { useTranslations } from "next-intl";
import Image from "next/image";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const t = useTranslations();

  useEffect(() => {
    console.error("Global Error:", error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen py-12 bg-gray-50">
      <Image
        src="/error.png"
        width={200}
        height={200}
        alt="Error illustration"
        className="mb-6"
        priority
      />

      <h1 className="mb-2 text-[40px] font-semibold leading-11.75 text-gray-900">
        {t("somethingWentWrong")}
      </h1>

      <p className="mb-6 text-[20px] font-light leading-6 text-gray-600 max-w-md text-center">
        {t("somethingWentWrongSubtitle")}
      </p>

      <div className="flex gap-4">
        <button
          onClick={() => reset()}
          className="flex items-center justify-center rounded-full bg-gray-900 px-8 py-1.5 text-lg font-medium text-white transition-all hover:bg-gray-800"
        >
          {t("retry")}
        </button>
        <button
          onClick={() => window.location.href = "/"}
          className="flex items-center justify-center rounded-full border border-gray-900 px-8 py-1.5 text-lg font-medium text-gray-900 transition-all hover:bg-gray-100"
        >
          {t("goBack")}
        </button>
      </div>

      {process.env.NODE_ENV === "development" && error.message && (
        <div className="mt-8 p-4 bg-red-50 border border-red-200 rounded-[10px] max-w-2xl">
          <p className="text-sm text-red-800 font-mono break-words">
            {error.message}
          </p>
        </div>
      )}
    </div>
  );
}
