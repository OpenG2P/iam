import { useMemo } from 'react';
import { useFetch } from '@/shared/hooks/useFetch';

export interface DataPolicy {
    policy_id: string;
    policy_mnemonic: string;
    policy_description: string;
    register_id: string;
    policy_target: string;
    policy_type: string;
    policy_filter_expression: Record<string, unknown>;
    application_id?: number;
}

export function usePolicies(
    registerId: string,
    policyTarget: string,
    applicationId?: number,
    currentPage: number = 1,
    pageSize: number = 10,
) {
    const enabled = policyTarget === 'ATTRIBUTE' || policyTarget === 'GEO' || !!registerId;

    const { data, loading, error, execute } = useFetch<{
        policies: DataPolicy[];
        pagination?: {
            number_of_items: number;
            number_of_pages: number;
        };
    }>({
        url: '/api/applications/data-policies/get-all',
        enabled,
        options: {
            method: 'POST',
            body: JSON.stringify({
                current_page: currentPage,
                page_size: pageSize,
                sort_by: '',
                search_text: '',
                filter_by: '',
                application_id: applicationId,
                policy_target: policyTarget,
                register_id: policyTarget === 'REGISTER_RECORD' ? registerId : null,
            }),
        },
    });

    const policies = data?.policies ?? [];

    return {
        policies,
        pagination: data?.pagination,
        loading,
        error,
        refresh: execute,
    };
}
