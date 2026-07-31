import { ButtonHTMLAttributes, ReactNode } from "react";

interface SecondaryButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className"> {
  children: ReactNode;
}

export default function SecondaryButton({ children, disabled = false, onClick, ...props }: SecondaryButtonProps) {
  return (
    <button
      type="button"
      className="inline-block text-[16px] font-medium px-4 py-2 rounded cursor-pointer text-decoration-none leading-[1.2] border-none transition-colors duration-150 bg-transparent text-[var(--color-black)] border border-[var(--color-border)] hover:bg-[var(--color-light-grey)] disabled:opacity-50 disabled:not-allowed"
      disabled={disabled}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  );
}
