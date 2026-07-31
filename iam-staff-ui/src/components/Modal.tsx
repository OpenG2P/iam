"use client";

import type { ReactNode } from "react";
import { X } from "lucide-react";

interface ModalProps {
  title: string;
  onClose: () => void;
  children: ReactNode;
  wide?: boolean;
}

export default function Modal({
  title,
  onClose,
  children,
  wide,
}: ModalProps) {
  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-[100] p-4"
      onClick={onClose}
      role="presentation"
    >
      <div
        className={`relative w-full bg-white rounded-[20px] shadow-lg max-h-[90vh] overflow-auto p-8 ${wide ? "max-w-[720px]" : "max-w-[560px]"}`}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X size={24} strokeWidth={2} />
        </button>
        <h2 className="text-[22px] font-bold text-black mb-6 mt-4">{title}</h2>
        {children}
      </div>
    </div>
  );
}
