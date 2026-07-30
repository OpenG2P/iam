"use client";

import { ReactNode } from "react";

interface Column<T> {
  key: string;
  header: string;
  render: (item: T) => ReactNode;
}

interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  onRowClick?: (item: T) => void;
  emptyMessage?: string;
}

export default function Table<T>({
  columns,
  data,
  onRowClick,
  emptyMessage = "No records found.",
}: TableProps<T>) {
  if (data.length === 0) {
    return (
      <div className="text-center py-10 px-4 text-gray-600">
        <p className="text-gray-600">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <table className="w-full border-collapse bg-[var(--color-surface)]">
      <thead>
        <tr>
          {columns.map((column) => (
            <th
              key={column.key}
              className="text-left py-3 px-9 border-b border-[var(--color-border)] font-medium text-[var(--color-text-muted)] text-[16px] uppercase tracking-wider bg-gray-50"
            >
              {column.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((item, index) => (
          <tr
            key={index}
            className={`cursor-pointer transition-colors duration-150 ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'} hover:bg-gray-100`}
            onClick={() => onRowClick?.(item)}
          >
            {columns.map((column) => (
              <td key={column.key} className="py-4 px-9 align-middle">
                {column.render(item)}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
