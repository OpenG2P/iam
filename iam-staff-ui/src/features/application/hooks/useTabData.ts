import { useCallback, useState } from "react";
import { useFetch } from "@/shared/hooks/useFetch";
import { useConfig } from "@/context/ConfigContext";

function extractList<T>(data: any): { items: T[]; total: number } {
  if (!data || data.error) return { items: [], total: 0 };
  const items = Array.isArray(data.items)
    ? data.items
    : Array.isArray(data)
      ? data
      : [];
  return {
    items,
    total: data.pagination?.number_of_items ?? data.pagination?.total ?? items.length,
  };
}

interface UseTabDataOptions {
  endpoint: string;
  applicationId: number;
}

export function useTabData<T>({ endpoint, applicationId }: UseTabDataOptions) {
  const { execute } = useFetch();
  const { pageSize } = useConfig();
  const [data, setData] = useState<T[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  const loadData = useCallback(
    async (p: number) => {
      setLoading(true);
      try {
        const result = await execute(endpoint, {
          method: "POST",
          body: JSON.stringify({
            application_id: applicationId,
            current_page: p,
            page_size: pageSize,
          }),
        });
        const { items, total } = extractList<T>(result);
        setData(items);
        setTotal(total);
      } finally {
        setLoading(false);
      }
    },
    [applicationId, execute, endpoint, pageSize],
  );

  const reset = useCallback(() => {
    setData([]);
    setTotal(0);
    setPage(1);
  }, []);

  return {
    data,
    total,
    page,
    loading,
    loadData,
    setPage,
    reset,
    execute,
  };
}
