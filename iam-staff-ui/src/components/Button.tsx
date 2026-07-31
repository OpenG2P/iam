"use client";

interface ButtonProps {
  children: React.ReactNode;
  type?: "button" | "submit" | "reset";
  variant?: "primary" | "secondary" | "danger";
  disabled?: boolean;
  onClick?: () => void;
  className?: string;
}

export default function Button({
  children,
  type = "button",
  variant = "primary",
  disabled = false,
  onClick,
  className = "",
}: ButtonProps) {
  const baseStyles = "inline-block text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 disabled:opacity-50 disabled:not-allowed";

  const variantStyles = {
    primary: "bg-[#f5bb1a] text-black hover:bg-[#e0a800]",
    secondary: "bg-transparent text-black border border-gray-300 hover:bg-gray-100",
    danger: "bg-red-500 text-white hover:bg-red-600",
  };

  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`${baseStyles} ${variantStyles[variant]} ${className}`}
    >
      {children}
    </button>
  );
}
