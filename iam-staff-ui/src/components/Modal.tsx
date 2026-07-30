"use client";

import type { ReactNode } from "react";

interface ModalProps {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
  wide?: boolean;
}

export default function Modal({
  open,
  title,
  onClose,
  children,
  wide,
}: ModalProps) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[1000] p-6"
      onClick={onClose}
      role="presentation"
    >
      <div
        className={`bg-white rounded-[10px] shadow-lg w-full max-h-[90vh] overflow-auto p-6 ${wide ? "max-w-[720px]" : "max-w-[560px]"}`}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="m-0 font-[var(--font-heading)] text-[20px] font-medium text-[var(--color-black)]">{title}</h2>
          <button
            type="button"
            className="bg-transparent border-none p-1 hover:opacity-70 transition-opacity"
            onClick={onClose}
          >
            <img src="/edit.png" alt="Close" className="w-5 h-5" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
