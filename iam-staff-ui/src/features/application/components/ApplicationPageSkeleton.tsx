"use client";

export default function ApplicationPageSkeleton() {
  return (
    <div>
      <div className="flex items-center justify-between gap-4 mb-3 relative">
        <div className="text-[24px] font-bold text-black mb-4 opacity-0">Application Name</div>
        <div className="absolute top-0 left-0 h-8 w-64 bg-gray-200 rounded animate-pulse" />
      </div>
      <div className="flex flex-wrap items-end gap-2 mb-0 ml-5">
        {["Application", "Roles", "Permissions", "Roles to Permissions", "Data Policies"].map((label, i) => (
          <div
            key={i}
            className="relative inline-flex items-center justify-center gap-1.5 min-w-30 max-w-45 px-6 py-3 border-none rounded-t-[10px] rounded-b-none bg-[#e1e1e1] text-black text-[18px] font-semibold leading-[1.3]"
          >
            <span className="block w-full overflow-hidden text-ellipsis whitespace-nowrap text-center opacity-0">
              {label}
            </span>
            <div className="absolute inset-0 bg-gray-200 rounded-t-[10px] animate-pulse" />
          </div>
        ))}
      </div>
      <div className="bg-white rounded-[10px] p-6 shadow-[0_1px_2px_rgba(6,19,39,0.05)]">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="flex flex-col gap-1.5 relative">
              <div className="text-sm opacity-0">Label</div>
              <div className="h-9.5 opacity-0">Value</div>
              <div className="absolute inset-0 flex flex-col gap-1.5">
                <div className="animate-pulse bg-gray-200 w-20 h-3 mb-2 rounded-sm" />
                <div className="animate-pulse bg-gray-200 w-full h-9.5 rounded-lg" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
