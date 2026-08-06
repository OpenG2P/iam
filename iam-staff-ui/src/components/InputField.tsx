"use client";

interface InputFieldProps {
  label?: string;
  value: string | number;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: string;
  disabled?: boolean;
  min?: number;
  max?: number;
  className?: string;
  required?: boolean;
}

export default function InputField({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
  disabled = false,
  min,
  max,
  className = "",
  required = false,
}: InputFieldProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const nextValue = e.target.value;
    if (nextValue !== "" && min !== undefined && Number(nextValue) < min) {
      return;
    }
    if (nextValue !== "" && max !== undefined && Number(nextValue) > max) {
      return;
    }
    onChange(nextValue);
  };

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
      <input
        type={type}
        value={value}
        placeholder={placeholder}
        disabled={disabled}
        min={min}
        max={max}
        required={required}
        onChange={handleChange}
        className={`w-full border border-[#ED7C22] py-2 px-4 rounded-[10px] outline-none text-[16px] text-[#000000] disabled:opacity-50 disabled:cursor-not-allowed ${label ? 'mt-2' : ''}`}
      />
    </div>
  );
}
