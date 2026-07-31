import { useTranslations } from "next-intl";
import Modal from "@/components/Modal";

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
  open: boolean;
  title: string;
  onClose: () => void;
  onSubmit: (e: React.FormEvent) => Promise<void>;
  saving: boolean;
  fields: FormField[];
  formData: Record<string, any>;
  onChange: (name: string, value: string) => void;
}

export default function FormModal({
  open,
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
    <Modal open={open} title={title} onClose={onClose}>
      <form onSubmit={onSubmit}>
        <div className="grid grid-cols-2 gap-4">
          {fields.map((field) => (
            <div key={field.name} className="flex flex-col gap-1.5 col-span-full">
              <label className="text-[16px] font-medium text-gray-600">
                {field.label}
                {field.required && " *"}
              </label>
              {field.type === "select" ? (
                <select
                  required={field.required}
                  className="font-sans text-[16px] p-2.5 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                  value={formData[field.name]}
                  onChange={(e) => onChange(field.name, e.target.value)}
                >
                  <option value="">{field.placeholder || "Select..."}</option>
                  {field.options?.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              ) : field.type === "textarea" ? (
                <textarea
                  required={field.required}
                  className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] min-h-[80px] resize-y"
                  value={formData[field.name]}
                  onChange={(e) => onChange(field.name, e.target.value)}
                  placeholder={field.placeholder}
                />
              ) : (
                <input
                  required={field.required}
                  type="text"
                  className="font-sans text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a]"
                  value={formData[field.name]}
                  onChange={(e) => onChange(field.name, e.target.value)}
                  placeholder={field.placeholder}
                />
              )}
              {field.helperText && (
                <span className="text-[16px] text-gray-400 mt-0.5">
                  {field.helperText}
                </span>
              )}
            </div>
          ))}
        </div>
        <div className="flex gap-3 justify-end mt-5 pt-4 border-t border-gray-100">
          <button
            type="button"
            className="inline-block font-sans text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-transparent text-black border border-gray-300 hover:bg-gray-100"
            onClick={onClose}
          >
            {t("cancel")}
          </button>
          <button
            type="submit"
            className="inline-block font-sans text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-[#f5bb1a] text-black hover:bg-[#e0a800] disabled:opacity-50 disabled:not-allowed"
            disabled={saving}
          >
            {saving ? t("saving") : t("save")}
          </button>
        </div>
      </form>
    </Modal>
  );
}
