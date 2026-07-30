"use client";

import { useEffect } from "react";
import { useTranslations } from "next-intl";
import Image from "next/image";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const t = useTranslations();

  useEffect(() => {
    console.error("Rendering Error:", error);
  }, [error]);

  const getErrorMessage = (error: Error) => {
    if (error.message.includes("fetch")) {
      return "Network error. Please check your connection.";
    }
    if (error.message.includes("timeout")) {
      return "Request timed out. Please try again.";
    }
    if (error.message.includes("401") || error.message.includes("403")) {
      return "Authentication error. You may need to log in again.";
    }
    if (error.message.includes("404")) {
      return "The requested resource was not found.";
    }
    if (error.message.includes("500")) {
      return "Server error. Please try again later.";
    }
    return error.message || t("something_went_wrong_subtitle");
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] py-12">
      <Image
        src="/error.png"
        width={200}
        height={200}
        alt="Error illustration"
        className="mb-6"
        priority
      />

      <h1 className="mb-2 text-[40px] font-semibold leading-11.75 text-gray-900">
        {t("something_went_wrong")}
      </h1>

      <p className="mb-6 text-[20px] font-light leading-6 text-gray-600 max-w-md text-center">
        {getErrorMessage(error)}
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
          {t("go_back")}
        </button>
      </div>

      {process.env.NODE_ENV === "development" && error.message && (
        <div className="mt-8 p-4 bg-red-50 border border-red-200 rounded-[10px] max-w-2xl">
          <p className="text-sm text-red-800 font-mono break-words">
            {error.message}
          </p>
          {error.stack && (
            <pre className="mt-2 text-xs text-red-700 font-mono overflow-auto max-h-40">
              {error.stack}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
