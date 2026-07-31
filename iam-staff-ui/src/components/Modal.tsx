"use client";

import type { ReactNode } from "react";
import { X } from "lucide-react";

interface ModalProps {
  title: string;
  onClose: () => void;
  children: ReactNode;
  width?: string;
}

export default function Modal({
  title,
  onClose,
  children,
  width = "600",
}: ModalProps) {
  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-100 p-4"
      onClick={onClose}
      role="presentation"
    >
      <div
        className={`relative w-full bg-white rounded-[10px] shadow-lg max-h-[80vh] p-8`}
        style={{ maxWidth: `${width}px` }}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-[22px] font-bold text-black">{title}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={30} />
          </button>
        </div>
        <div className="modal-scroll overflow-y-auto max-h-[calc(80vh-120px)] pr-2">
          {children}
        </div>
      </div>
    </div>
  );
}
