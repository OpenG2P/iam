import { useCallback, useState, useRef } from "react";
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
  const [loading, setLoading] = useState(true);
  const [loadedOnce, setLoadedOnce] = useState(false);

  // Use ref to store latest values for stable callback
  const latestValues = useRef({ applicationId, endpoint, pageSize, execute });
  latestValues.current = { applicationId, endpoint, pageSize, execute };

  const loadData = useCallback(
    async (p: number) => {
      setLoading(true);
      try {
        const { applicationId, endpoint, pageSize, execute } = latestValues.current;
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
        setLoadedOnce(true);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const reset = useCallback(() => {
    setData([]);
    setTotal(0);
    setPage(1);
    setLoadedOnce(false);
  }, []);

  return {
    data,
    total,
    page,
    loading,
    loadedOnce,
    loadData,
    setPage,
    reset,
    execute,
  };
}
