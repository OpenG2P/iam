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
    <div className={`flex flex-col gap-1.5 ${className}`}>
      {label && (
        <label className="text-[16px] font-medium text-gray-600">
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
        className="text-[16px] p-2 border border-gray-300 rounded bg-white text-black focus:outline-2 focus:outline-[rgba(245,187,26,0.45)] focus:border-[#f5bb1a] min-h-[80px] resize-y disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
      />
    </div>
  );
}
