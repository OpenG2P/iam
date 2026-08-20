import { useMemo } from 'react';
import { useFetch } from '@/shared/hooks/useFetch';
import { getCsrfTokenFromDocument } from '@/shared/utils/csrf';

export interface Register {
    register_id: string;
    register_mnemonic: string;
    register_rank?: number;
}

export function useAllRegister(
    apiUrl?: string | null,
    page?: number,
    pageSize?: number,
) {
    const { data, loading, error, execute } = useFetch<{
        registers: Register[];
        pagination?: {
            number_of_items: number;
            number_of_pages: number;
        };
    }>({
        url: '/api/registry/registers/all',
        enabled: !!apiUrl,
        options: {
            method: 'POST',
            body: JSON.stringify({
                api_url: apiUrl,
                csrf_token: getCsrfTokenFromDocument(),
                current_page: page,
                page_size: pageSize
            })
        }
    });

    // Ascending order
    const registers = (data?.registers || [])
        .sort((a, b) => (a.register_rank ?? 0) - (b.register_rank ?? 0));

    return {
        registers,
        pagination: data?.pagination,
        loading,
        error,
        refresh: execute,
    };
}
