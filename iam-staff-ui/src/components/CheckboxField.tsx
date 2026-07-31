"use client";

interface CheckboxFieldProps {
  label?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  className?: string;
}

export default function CheckboxField({
  label,
  checked,
  onChange,
  disabled = false,
  className = "",
}: CheckboxFieldProps) {
  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      <label className="text-[16px] font-medium text-gray-600">
        <input
          type="checkbox"
          className="w-5 h-5"
          checked={checked}
          disabled={disabled}
          onChange={(e) => onChange(e.target.checked)}
        />{" "}
        {label}
      </label>
    </div>
  );
}
