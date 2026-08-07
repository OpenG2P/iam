"use client";

import { useRef } from "react";
import { useTranslations } from "next-intl";
import { SecondaryButton } from "@/components";
import { fileToBase64, iconDataUrl, detectMimeType } from "@/shared/utils/iconBase64";

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
  mimeType,
  onChange,
  onClear,
  disabled = false,
}: IconBase64FieldProps) {
  const t = useTranslations();
  const inputRef = useRef<HTMLInputElement>(null);
  const detectedMimeType = value ? detectMimeType(value) : mimeType || "image/png";
  const previewSrc = iconDataUrl(value, detectedMimeType);

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
    <div className="flex flex-col gap-2 col-span-full">
      <label className="text-[16px] font-medium text-black">{label ?? t("icon")}</label>
      <div className="flex items-center gap-4">
        <div className="shrink-0 w-16 h-16 border border-[#ED7C22] rounded-[10px] bg-(--color-surface) flex items-center justify-center overflow-hidden">
          {previewSrc ? (
            <img src={previewSrc} alt="" className="w-full h-full object-contain p-1.5" />
          ) : (
            <span className="text-[12px] leading-tight text-black text-center px-1.5">
              {t("noIcon")}
            </span>
          )}
        </div>

        <div className="flex flex-col gap-1.5 min-w-0">
          <div className="flex flex-wrap gap-2">
            <input
              ref={inputRef}
              type="file"
              accept="image/*"
              className="hidden"
              disabled={disabled}
              onChange={handleFileChange}
            />
            <SecondaryButton
              disabled={disabled}
              onClick={() => inputRef.current?.click()}
            >
              {previewSrc ? t("changeIcon") : t("uploadIcon")}
            </SecondaryButton>
            {previewSrc && !disabled && (
              <SecondaryButton onClick={() => onClear?.()}>
                {t("removeIcon")}
              </SecondaryButton>
            )}
          </div>
          <span className="text-[13px] text-(--color-text-muted)">Supports SVG, PNG, JPEG, GIF, BMP</span>
        </div>
      </div>
    </div>
  );
}
