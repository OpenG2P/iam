"use client";

import { useTranslations } from "next-intl";
import Modal from "./Modal";

interface ConfirmModalProps {
  open: boolean;
  title?: string;
  warningText?: string;
  confirming?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmModal({
  open,
  title,
  warningText,
  confirming,
  onConfirm,
  onCancel,
}: ConfirmModalProps) {
  const t = useTranslations();

  return (
    <Modal open={open} title={title || t("confirm")} onClose={onCancel}>
      {warningText && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4 mb-4">
          <p className="text-[16px] text-yellow-800 m-0">
            <span className="font-semibold">{t("warning")}: </span>
            {warningText}
          </p>
        </div>
      )}
      <div className="flex gap-3 justify-end">
        <button
          type="button"
          className="inline-block font-sans text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-transparent text-black border border-gray-300 hover:bg-gray-100 disabled:opacity-50 disabled:not-allowed"
          onClick={onCancel}
          disabled={confirming}
        >
          {t("cancel")}
        </button>
        <button
          type="button"
          className="inline-block font-sans text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-[var(--color-danger)] text-white hover:bg-[#a93226] disabled:opacity-50 disabled:not-allowed flex items-center gap-2"
          onClick={onConfirm}
          disabled={confirming}
        >
          {confirming && (
            <svg
              className="animate-spin h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
          )}
          {t("delete")}
        </button>
      </div>
    </Modal>
  );
}
