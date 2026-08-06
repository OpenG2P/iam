"use client";

import { useTranslations } from "next-intl";
import {
  IconBase64Field,
  InputField,
  Modal,
  TextAreaField,
  Button,
} from "@/components";

interface ApplicationForm {
  application_mnemonic: string;
  application_description: string;
  application_url: string;
  order: string;
  width: string;
  icon_base64: string;
  icon_mime_type: string;
}

interface ApplicationModalProps {
  onClose: () => void;
  form: ApplicationForm;
  onChange: (field: keyof ApplicationForm, value: any) => void;
  onSave: (e: React.FormEvent) => Promise<void>;
  saving: boolean;
}

const emptyForm: ApplicationForm = {
  application_mnemonic: "",
  application_description: "",
  application_url: "",
  order: "",
  width: "",
  icon_base64: "",
  icon_mime_type: "image/png",
};

export default function ApplicationModal({
  onClose,
  form,
  onChange,
  onSave,
  saving,
}: ApplicationModalProps) {
  const t = useTranslations();

  return (
    <Modal title="Add Application" onClose={onClose}>
      <form onSubmit={onSave}>
        <div className="grid grid-cols-2 gap-4">
          <InputField
            label="Mnemonic"
            value={form.application_mnemonic}
            onChange={(value) => onChange("application_mnemonic", value)}
            className="col-span-full"
            required
          />
          <TextAreaField
            label="Description"
            value={form.application_description}
            onChange={(value) => onChange("application_description", value)}
            className="col-span-full"
            rows={1}
          />
          <InputField
            label="URL"
            value={form.application_url}
            onChange={(value) => onChange("application_url", value)}
            className="col-span-full"
          />
          <InputField
            label="Order"
            type="number"
            value={form.order}
            onChange={(value) => onChange("order", value)}
          />
          <InputField
            label="Width"
            type="number"
            value={form.width}
            onChange={(value) => onChange("width", value)}
          />
          <IconBase64Field
            value={form.icon_base64}
            mimeType={form.icon_mime_type}
            onChange={(base64, mimeType) => {
              onChange("icon_base64", base64);
              onChange("icon_mime_type", mimeType);
            }}
            onClear={() => {
              onChange("icon_base64", "");
              onChange("icon_mime_type", "image/png");
            }}
          />
        </div>
        <div className="flex gap-3 justify-end mt-5">
          <Button type="button" variant="secondary" onClick={onClose}>
            {t("cancel")}
          </Button>
          <Button type="submit" variant="primary" disabled={saving}>
            {saving ? t("saving") : t("save")}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export { emptyForm };
