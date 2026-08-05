'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { Plus, X } from 'lucide-react';
import type { GeoLevel } from '../hooks/useG2pGeoLevels';
import GeoLocationPickerModal from './GeoLocationPickerModal';
import type { GeoLocationSelection } from '../types/geoLocationTypes';
import { geoHierarchyKey, mergeGeoLocationSelections } from '../utils/geoLocationSerialization';

interface AdministrativeAreasPolicyBuilderProps {
    geoLevels: GeoLevel[];
    geoLevelsLoading?: boolean;
    locations: GeoLocationSelection[];
    onChange: (locations: GeoLocationSelection[]) => void;
    disabled?: boolean;
}

export default function AdministrativeAreasPolicyBuilder({
    geoLevels,
    geoLevelsLoading,
    locations,
    onChange,
    disabled,
}: AdministrativeAreasPolicyBuilderProps) {
    const t = useTranslations();
    const [pickerOpen, setPickerOpen] = useState(false);

    const handleRemove = (selection: GeoLocationSelection) => {
        const key = geoHierarchyKey(selection.hierarchy);
        onChange(locations.filter((item) => geoHierarchyKey(item.hierarchy) !== key));
    };

    const handleConfirm = (incoming: GeoLocationSelection[]) => {
        onChange(mergeGeoLocationSelections(locations, incoming));
    };

    if (!geoLevels.length && !geoLevelsLoading) {
        return (
            <p className="text-[16px] text-[#000000]/50">
                {t('no_geo_levels_for_filter_fields')}
            </p>
        );
    }

    return (
        <>
            <div className="flex flex-col gap-4">
                <div className="inline-flex w-fit items-center gap-2 rounded-full border border-[#ED7C22]/30 bg-[#F3F1E4]/40 px-3 py-1.5 text-sm text-[#000000]/70">
                    <span>{t('geo_grouping_logic_label')}</span>
                    <span className="rounded bg-[#000000] px-2 py-0.5 text-xs font-bold text-[#FFFFFF]">
                        {t('filter_logic_and')}
                    </span>
                    <span className="text-[#000000]/50">{t('geo_grouping_logic_hint')}</span>
                </div>

                {locations.length === 0 ? (
                    <div className="rounded-[10px] border-2 border-dashed border-[#ED7C22]/30 px-6 py-8 text-center">
                        <p className="text-sm text-[#000000]/70">{t('no_admin_locations_added')}</p>
                        <p className="mt-1 text-xs text-[#000000]/50">
                            {t('no_admin_locations_hint')}
                        </p>
                    </div>
                ) : (
                    <div className="flex flex-col gap-2">
                        {locations.map((selection) => (
                            <div
                                key={geoHierarchyKey(selection.hierarchy)}
                                className="flex items-center justify-between rounded-[10px] border border-[#ED7C22]/30 bg-[#ED7C22]/5 px-4 py-3"
                            >
                                <div className="min-w-0">
                                    <div className="truncate text-sm font-semibold text-[#000000]">
                                        {selection.displayName}
                                    </div>
                                    {selection.displayPath ? (
                                        <div className="truncate text-xs text-[#000000]/50">
                                            {selection.displayPath}
                                        </div>
                                    ) : null}
                                </div>
                                <button
                                    type="button"
                                    disabled={disabled}
                                    onClick={() => handleRemove(selection)}
                                    className="ml-3 shrink-0 text-red-500 hover:opacity-80 disabled:opacity-50"
                                    aria-label={t('remove')}
                                >
                                    <X size={18} />
                                </button>
                            </div>
                        ))}
                    </div>
                )}

                <button
                    type="button"
                    disabled={disabled || geoLevelsLoading || !geoLevels.length}
                    onClick={() => setPickerOpen(true)}
                    className="inline-flex w-fit items-center gap-2 rounded-[10px] border border-[#ED7C22]/40 bg-[#FFFFFF] px-4 py-2 text-sm font-semibold text-[#000000] hover:bg-[#F3F1E4]/40 disabled:cursor-not-allowed disabled:opacity-50"
                >
                    <Plus size={16} />
                    {t('add_admin_location')}
                </button>
            </div>

            {pickerOpen ? (
                <GeoLocationPickerModal
                    geoLevels={geoLevels}
                    onClose={() => setPickerOpen(false)}
                    onConfirm={handleConfirm}
                />
            ) : null}
        </>
    );
}
