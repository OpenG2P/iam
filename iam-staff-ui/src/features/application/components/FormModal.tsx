import { useTranslations } from "next-intl";
import {
  Button,
  FormActions,
  InputField,
  Modal,
  SelectField,
  TextAreaField,
} from "@/components";

interface FormField {
  name: string;
  label: string;
  type: "text" | "textarea" | "select";
  required?: boolean;
  options?: { value: string; label: string }[];
  placeholder?: string;
  helperText?: string;
}

interface FormModalProps {
  title: string;
  onClose: () => void;
  onSubmit: (e: React.FormEvent) => Promise<void>;
  saving: boolean;
  fields: FormField[];
  formData: Record<string, any>;
  onChange: (name: string, value: string) => void;
}

export default function FormModal({
  title,
  onClose,
  onSubmit,
  saving,
  fields,
  formData,
  onChange,
}: FormModalProps) {
  const t = useTranslations();

  return (
    <Modal title={title} onClose={onClose}>
      <form onSubmit={onSubmit}>
        <div className="grid grid-cols-2 gap-4">
          {fields.map((field) => (
            <div key={field.name} className="flex flex-col gap-1.5 col-span-full">
              {field.type === "select" ? (
                <SelectField
                  label={field.label}
                  value={formData[field.name]}
                  onChange={(value) => onChange(field.name, value)}
                  options={field.options || []}
                  placeholder={field.placeholder}
                  required={field.required}
                />
              ) : field.type === "textarea" ? (
                <TextAreaField
                  label={`${field.label}${field.required ? " *" : ""}`}
                  value={formData[field.name]}
                  onChange={(value) => onChange(field.name, value)}
                  placeholder={field.placeholder}
                  rows={4}
                  required={field.required}
                />
              ) : (
                <InputField
                  label={`${field.label}${field.required ? " *" : ""}`}
                  value={formData[field.name]}
                  onChange={(value) => onChange(field.name, value)}
                  placeholder={field.placeholder}
                  required={field.required}
                />
              )}
              {field.helperText && (
                <span className="text-[16px] text-gray-600 mt-0.5">
                  {field.helperText}
                </span>
              )}
            </div>
          ))}
        </div>
        <FormActions>
          <Button type="button" variant="secondary" onClick={onClose}>
            {t("cancel")}
          </Button>
          <Button type="submit" variant="primary" disabled={saving}>
            {saving ? t("saving") : t("save")}
          </Button>
        </FormActions>
      </form>
    </Modal>
  );
}
