import { useMemo } from 'react';
import { useFetch } from '@/shared/hooks/useFetch';
import { getCsrfTokenFromDocument } from '@/shared/utils/csrf';

export interface RegisterField {
    field_name: string;
    data_type: string;
    required: boolean;
    nullable: boolean;
}

type RegisterFieldsResponse = {
    register_id?: string;
    register_mnemonic?: string;
    fields?: RegisterField[];
    pagination?: {
        number_of_items: number;
        number_of_pages: number;
    };
    error?: string;
};

export function useRegisterFields(registerId: string, apiUrl?: string | null) {
    const fetchOptions = useMemo(
        () => ({
            method: 'POST' as const,
            body: JSON.stringify({
                api_url: apiUrl,
                csrf_token: getCsrfTokenFromDocument(),
                register_id: registerId,
                current_page: 1,
                page_size: 500,
            }),
        }),
        [apiUrl, registerId],
    );

    const { data, loading, error, execute } = useFetch<RegisterFieldsResponse>({
        url: '/api/registry/registers/register-fields',
        enabled: !!registerId && !!apiUrl,
        options: fetchOptions,
    });

    const fields = data?.error ? [] : data?.fields ?? [];

    return {
        fields,
        registerMnemonic: data?.register_mnemonic,
        loading,
        error: error ?? data?.error ?? null,
        refresh: execute,
    };
}
