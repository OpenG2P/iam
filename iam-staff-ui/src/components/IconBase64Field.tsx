"use client";

import { useRef } from "react";
import { useTranslations } from "next-intl";
import { fileToBase64, iconDataUrl } from "@/shared/utils/iconBase64";

type IconBase64FieldProps = {
  label?: string;
  value: string;
  mimeType?: string;
  onChange: (base64: string, mimeType: string) => void;
  onClear?: () => void;
  disabled?: boolean;
};

export default function IconBase64Field({
  label,
  value,
  mimeType = "image/png",
  onChange,
  onClear,
  disabled = false,
}: IconBase64FieldProps) {
  const t = useTranslations();
  const inputRef = useRef<HTMLInputElement>(null);
  const previewSrc = iconDataUrl(value, mimeType);

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      return;
    }
    const base64 = await fileToBase64(file);
    onChange(base64, file.type);
  }

  return (
    <div className="flex flex-col gap-1.5 col-span-full">
      <label className="text-[16px] font-medium text-[var(--color-text-muted)]">{label ?? t("icon")}</label>
      <div className="flex flex-col gap-3">
        {previewSrc ? (
          <div className="w-[72px] h-[72px] border border-[var(--color-border)] rounded-[10px] bg-[var(--color-surface)] flex items-center justify-center overflow-hidden">
            <img src={previewSrc} alt="" className="max-w-full max-h-full object-contain" />
          </div>
        ) : (
          <div className="w-[72px] h-[72px] border border-[var(--color-border)] rounded-[10px] bg-[var(--color-surface)] flex items-center justify-center overflow-hidden">
            <span className="text-[16px] text-[var(--color-text-muted)] text-center p-2">{t("noIcon")}</span>
          </div>
        )}
        <div className="flex flex-wrap gap-2 items-center">
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            className="hidden"
            disabled={disabled}
            onChange={handleFileChange}
          />
          <button
            type="button"
            className="inline-block text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-transparent text-[var(--color-black)] border border-[var(--color-border)] hover:bg-[var(--color-light-grey)] disabled:opacity-50 disabled:not-allowed"
            disabled={disabled}
            onClick={() => inputRef.current?.click()}
          >
            {previewSrc ? t("changeIcon") : t("uploadIcon")}
          </button>
          {previewSrc && !disabled && (
            <button
              type="button"
              className="inline-block text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-transparent text-[var(--color-black)] border border-[var(--color-border)] hover:bg-[var(--color-light-grey)] disabled:opacity-50 disabled:not-allowed"
              onClick={() => onClear?.()}
            >
              {t("removeIcon")}
            </button>
          )}
        </div>
        <span className="text-[16px] text-[var(--color-text-muted)]">{t("iconHint")}</span>
      </div>
    </div>
  );
}
