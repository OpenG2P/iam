"use client";

type TableSkeletonProps = {
  rows?: number;
  columns?: number;
  headers?: string[];
};

export default function TableSkeleton({
  rows = 5,
  columns = 4,
  headers,
}: TableSkeletonProps) {
  const colCount = headers ? headers.length : columns;

  // Generate slightly different widths for skeleton blocks to make them look more natural
  const getWidth = (colIndex: number) => {
    if (colIndex === colCount - 1) return "60px"; // Status column
    const widths = ["120px", "240px", "180px", "150px"];
    return widths[colIndex % widths.length];
  };

  return (
    <div className="overflow-x-auto" aria-hidden>
      <table className="w-full border-collapse bg-[var(--color-surface)]">
        {headers && (
          <thead>
            <tr>
              {headers.map((h, i) => (
                <th key={i} className="text-left pb-3 px-9 border-b border-[var(--color-border)] font-medium text-[var(--color-text-muted)] text-[16px] uppercase tracking-wider bg-gray-50">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
        )}
        <tbody>
          {Array.from({ length: rows }).map((_, rowIndex) => (
            <tr key={rowIndex} className={rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              {Array.from({ length: colCount }).map((__, colIndex) => (
                <td key={colIndex} className="py-4 px-9 align-middle">
                  <div
                    className="h-[14px] rounded-md bg-gradient-to-r from-[rgba(196,196,196,0.25)] via-[rgba(196,196,196,0.12)] to-[rgba(196,196,196,0.25)] bg-[length:200%_100%] animate-[shimmer_1.2s_ease-in-out_infinite]"
                    style={{ width: getWidth(colIndex) }}
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
