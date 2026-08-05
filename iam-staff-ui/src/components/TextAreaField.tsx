"use client";

interface TextAreaFieldProps {
  label?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  rows?: number;
  className?: string;
  required?: boolean;
}

export default function TextAreaField({
  label,
  value,
  onChange,
  placeholder,
  disabled = false,
  rows = 3,
  className = "",
  required = false,
}: TextAreaFieldProps) {
  return (
    <div>
      {label && (
        <label
          className="block text-[16px] font-medium text-[#000000] truncate"
          title={label}
        >
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <textarea
        value={value}
        placeholder={placeholder}
        disabled={disabled}
        required={required}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        className={`w-full border border-[#ED7C22] py-2 px-4 rounded-[10px] outline-none text-[16px] text-[#000000] disabled:opacity-50 disabled:cursor-not-allowed ${label ? 'mt-2' : ''}`}
      />
    </div>
  );
}
