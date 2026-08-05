import { useFetch } from '@/shared/hooks/useFetch';

export interface Attribute {
    attribute_code: string;
    attribute_display?: string;
}

export interface PaginationMeta {
    number_of_items: number;
    number_of_pages: number;
}

export function useAllAttributes(
    page?: number,
    pageSize?: number,
    searchText?: string,
) {
    const { data, loading, error, execute } = useFetch<{
        attributes: Attribute[];
        pagination?: PaginationMeta;
    }>({
        url: '/api/registry/attributes/all',
        options: {
            method: 'POST',
            body: JSON.stringify({
                current_page: page,
                page_size: pageSize,
                search_text: searchText ?? '',
            }),
        },
    });

    return {
        attributes: data?.attributes ?? [],
        pagination: data?.pagination,
        loading,
        error,
        refresh: execute,
    };
}
