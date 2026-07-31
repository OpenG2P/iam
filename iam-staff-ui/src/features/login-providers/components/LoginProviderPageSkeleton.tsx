"use client";

import BackLink from "@/components/BackLink";

export default function LoginProviderPageSkeleton() {
  return (
    <div>
      <BackLink href="/login-providers" />
      <div className="flex items-center justify-between gap-4 mb-6">
        <div className="animate-pulse bg-gray-200 w-[220px] h-[28px] rounded-[8px]" />
      </div>
      <div className="bg-white rounded-[10px] p-6 shadow-[0_1px_2px_rgba(6,19,39,0.05)]">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 12 }).map((_, i) => (
            <div key={i} className="flex flex-col gap-1.5">
              <div className="animate-pulse bg-gray-200 w-[80px] h-[12px] mb-2 rounded-[4px]" />
              <div className="animate-pulse bg-gray-200 w-full h-[38px] rounded-[8px]" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
