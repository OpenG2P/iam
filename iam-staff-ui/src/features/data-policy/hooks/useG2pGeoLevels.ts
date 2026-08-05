import { useFetch } from '@/shared/hooks/useFetch';

export interface GeoLevel {
    level_id: string;
    level_mnemonic: string;
    parent_level_id: string | null;
}

export function useG2pGeoLevels() {
    const { data, loading, error, execute } = useFetch<GeoLevel[]>({
        url: '/api/master-data/get-all-g2p-geo-levels',
        options: {
            method: 'POST',
            body: JSON.stringify({
                current_page: 1,
                page_size: 500,
            }),
        },
    });

    return {
        geoLevels: Array.isArray(data) ? data : [],
        loading,
        error,
        refresh: execute,
    };
}
