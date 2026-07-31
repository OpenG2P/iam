"use client";

import { useTranslations } from "next-intl";
import { useRbac } from "@/context/RbacContext";
import InputField from "@/components/InputField";
import TextAreaField from "@/components/TextAreaField";
import IconBase64Field from "@/components/IconBase64Field";
import Button from "@/components/Button";
import { Application, ApplicationForm } from "@/features/application/types";

interface ApplicationTabProps {
  app: Application;
  appForm: ApplicationForm;
  saving: boolean;
  setAppForm: (form: any) => void;
  saveApplication: (e: React.FormEvent) => Promise<void>;
}

export default function ApplicationTab({
  app,
  appForm,
  saving,
  setAppForm,
  saveApplication,
}: ApplicationTabProps) {
  const t = useTranslations();
  const { can } = useRbac();
  const isSelfRegistered = app.is_self_registered ?? false;
  const isDisabled = isSelfRegistered || !can("application:edit") || saving;

  return (
    <div className="bg-white rounded-[10px] p-6 shadow-[0_1px_2px_rgba(6,19,39,0.05)]">
      <form onSubmit={saveApplication}>
        <div className="grid grid-cols-2 gap-4">
          <InputField
            label="Mnemonic"
            value={app.application_mnemonic}
            onChange={() => {}}
            disabled
          />

          <InputField
            label="Self-registered"
            value={isSelfRegistered ? "Yes" : "No"}
            onChange={() => {}}
            disabled
          />

          <TextAreaField
            label="Description"
            value={appForm.application_description}
            onChange={(value) =>
              setAppForm((f: typeof appForm) => ({
                ...f,
                application_description: value,
              }))
            }
            disabled={isDisabled}
            rows={4}
            className="col-span-full"
          />

          <InputField
            label="URL"
            value={appForm.application_url}
            onChange={(value) =>
              setAppForm((f: typeof appForm) => ({
                ...f,
                application_url: value,
              }))
            }
            disabled={isDisabled}
            className="col-span-full"
          />

          <InputField
            label="Order"
            type="number"
            value={appForm.order}
            onChange={(value) =>
              setAppForm((f: typeof appForm) => ({ ...f, order: value }))
            }
            disabled={isDisabled}
          />

          <InputField
            label="Width"
            type="number"
            value={appForm.width}
            onChange={(value) =>
              setAppForm((f: typeof appForm) => ({ ...f, width: value }))
            }
            disabled={isDisabled}
          />

          <div className="col-span-full">
            <IconBase64Field
              value={appForm.icon_base64}
              mimeType={appForm.icon_mime_type}
              disabled={isDisabled}
              onChange={(base64, mimeType) =>
                setAppForm((f: typeof appForm) => ({
                  ...f,
                  icon_base64: base64,
                  icon_mime_type: mimeType,
                }))
              }
              onClear={() =>
                setAppForm((f: typeof appForm) => ({
                  ...f,
                  icon_base64: "",
                  icon_mime_type: "image/png",
                }))
              }
            />
          </div>
        </div>
        {!isSelfRegistered && (
          <div className="flex gap-3 justify-end mt-5 pt-4 border-t border-gray-100">
            <Button type="submit" variant="primary" disabled={saving}>
              {saving ? t("saving") : t("save")}
            </Button>
          </div>
        )}
      </form>
    </div>
  );
}
