import { useFetch } from '@/shared/hooks/useFetch';

export interface GeoLevelValue {
    level_value_id: string;
    level_id: string;
    level_value_mnemonic: string;
    parent_level_value_id: string;
}

export function getGeoLevelValueLabel(value: GeoLevelValue): string {
    return value.level_value_mnemonic || value.level_value_id;
}

export function useGeoLevelValues(
    levelId?: string,
    parentLevelValueId?: string,
    page = 1,
    pageSize = 500,
) {
    const { data, loading, error, execute } = useFetch<GeoLevelValue[]>({
        url: '/api/master-data/geo-level-values',
        enabled: !!levelId,
        options: {
            method: 'POST',
            body: JSON.stringify({
                current_page: page,
                page_size: pageSize,
                sort_by: '',
                search_text: '',
                level_id: levelId,
                parent_level_value_id: parentLevelValueId ?? '',
            }),
        },
    });

    const geoLevelValues = Array.isArray(data) ? data : [];

    return {
        geoLevelValues,
        allGeoLevelValues: geoLevelValues,
        loading,
        error,
        refresh: execute,
    };
}
