"use client";

interface SelectFieldProps {
  label?: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  className?: string;
}

export default function SelectField({
  label,
  value,
  onChange,
  options,
  placeholder = "Select...",
  disabled = false,
  required = false,
  className = "",
}: SelectFieldProps) {
  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      {label && (
        <label className="text-[16px] font-medium text-gray-600">
          {label}
          {required && " *"}
        </label>
      )}
      <select
        value={value}
        disabled={disabled}
        required={required}
        onChange={(e) => onChange(e.target.value)}
        className="text-[16px] p-2.5 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
      >
        <option value="">{placeholder}</option>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}
