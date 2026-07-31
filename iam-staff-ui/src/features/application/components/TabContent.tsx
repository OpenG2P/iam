import { useTranslations } from "next-intl";
import { useFetch } from "@/shared/hooks/useFetch";
import { toast } from "react-toastify";
import AddButton from "@/components/AddButton";
import Can from "@/components/Can";
import Table from "@/components/Table";
import TableSkeleton from "@/components/TableSkeleton";
import Pagination from "@/components/Pagination";
import { useConfig } from "@/context/ConfigContext";

interface Column<T> {
  key: string;
  header: string;
  render: (item: T) => React.ReactNode;
}

interface TabContentProps<T> {
  title: string;
  data: T[];
  total: number;
  page: number;
  loading: boolean;
  createAction: string;
  deleteAction: string;
  columns: Column<T>[];
  onPageChange: (page: number) => void;
  onAdd: () => void;
  showAddButton?: boolean;
}

export default function TabContent<T>({
  title,
  data,
  total,
  page,
  loading,
  createAction,
  deleteAction,
  columns,
  onPageChange,
  onAdd,
  showAddButton = true,
}: TabContentProps<T>) {
  const t = useTranslations();
  const { pageSize } = useConfig();

  return (
    <div className="bg-white rounded-[10px] pb-6 shadow-[0_1px_2px_rgba(6,19,39,0.05)]">
      <div className="flex items-center justify-between gap-4 mb-0 px-9 pt-6 pb-4">
        <h2 className="m-0 font-[var(--font-heading)] text-[20px] font-medium text-[var(--color-black)]">
          {title}
        </h2>
        {showAddButton && (
          <Can action={createAction}>
            <AddButton onClick={onAdd} />
          </Can>
        )}
      </div>
      {loading ? (
        <TableSkeleton rows={5} columns={columns.length} />
      ) : (
        <Table columns={columns} data={data} emptyMessage={t("noData")} />
      )}
      {!loading && data.length > 0 && (
        <Pagination
          page={page}
          pageSize={pageSize}
          total={total}
          onPageChange={onPageChange}
        />
      )}
    </div>
  );
}
