import { useFetch } from '@/shared/hooks/useFetch';

export interface AttributeValue {
    value_id: string;
    value_code: string;
    value_display?: string;
}

export function useAttributeValues(attributeId?: string) {
    const { data, loading, error, execute } = useFetch<{
        attributeValues: AttributeValue[];
    }>({
        url: '/api/master-data/attributes/values',
        enabled: !!attributeId,
        options: {
            method: 'POST',
            body: JSON.stringify({
                attribute_id: attributeId,
                current_page: 1,
                page_size: 1000,
            }),
        },
    });

    return {
        attributeValues: data?.attributeValues ?? [],
        loading,
        error,
        refresh: execute,
    };
}
