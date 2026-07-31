import { useTranslations } from "next-intl";
import {
  AddButton,
  Can,
  Card,
  Pagination,
  Table,
  TableSkeleton,
} from "@/components";
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
  loadedOnce?: boolean;
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
  loadedOnce = false,
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
    <Card padding="sm" className="pb-6">
      <div className="flex items-center justify-between gap-4 mb-0 px-9 pt-6 pb-4">
        {loading && !loadedOnce ? (
          <div className="h-7 w-48 bg-gray-200 rounded animate-pulse" />
        ) : (
          <h2 className="m-0 font-[var(--font-heading)] text-[20px] font-medium text-[var(--color-black)]">
            {title}
          </h2>
        )}
        {showAddButton && !(loading && !loadedOnce) && (
          <Can action={createAction}>
            <AddButton onClick={onAdd} />
          </Can>
        )}
        {loading && !loadedOnce && showAddButton && (
          <div className="h-10 w-32 bg-gray-200 rounded animate-pulse" />
        )}
      </div>
      {loading && !loadedOnce ? (
        <TableSkeleton rows={5} headers={columns.map(c => c.header)} />
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
    </Card>
  );
}
