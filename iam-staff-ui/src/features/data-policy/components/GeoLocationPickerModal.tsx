'use client';

import { useEffect, useMemo, useState } from 'react';
import { useTranslations } from 'next-intl';
import { ChevronRight, Search, X } from 'lucide-react';
import type { GeoLevel } from '../hooks/useG2pGeoLevels';
import type { GeoLevelValue } from '../hooks/useGeoLevelValues';
import {
    getChildLevels,
    getRootLevels,
    orderGeoLevelsByHierarchy,
} from '../utils/geoLevelUtils';
import { geoHierarchyKey, selectionFromHierarchy } from '../utils/geoLocationSerialization';
import type { GeoHierarchyRecord, GeoLocationSelection } from '../types/geoLocationTypes';

type BreadcrumbItem = {
    levelId: string;
    levelMnemonic: string;
    levelValueId: string;
    levelValueMnemonic: string;
    label: string;
};

interface GeoLocationPickerModalProps {
    geoLevels: GeoLevel[];
    onClose: () => void;
    onConfirm: (selections: GeoLocationSelection[]) => void;
}

async function fetchGeoLevelValues(
    levelId: string,
    parentLevelValueId: string,
): Promise<GeoLevelValue[]> {
    const response = await fetch('/api/master-data/geo-level-values', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            current_page: 1,
            page_size: 500,
            sort_by: '',
            search_text: '',
            level_id: levelId,
            parent_level_value_id: parentLevelValueId,
        }),
    });
    const payload = await response.json();
    const values = Array.isArray(payload) ? (payload as GeoLevelValue[]) : [];
    return values.map((value) => ({
        ...value,
        level_id: value.level_id || levelId,
    }));
}

function GeoChildCountBadge({
    childLevelIds,
    parentLevelValueId,
}: {
    childLevelIds: string[];
    parentLevelValueId: string;
}) {
    const t = useTranslations();
    const [count, setCount] = useState<number | null>(null);
    const idsKey = childLevelIds.join('|');

    useEffect(() => {
        if (!idsKey) {
            setCount(0);
            return;
        }

        let cancelled = false;
        Promise.all(
            idsKey.split('|').map((levelId) => fetchGeoLevelValues(levelId, parentLevelValueId)),
        ).then((groups) => {
            if (!cancelled) {
                setCount(groups.reduce((total, group) => total + group.length, 0));
            }
        });

        return () => {
            cancelled = true;
        };
    }, [idsKey, parentLevelValueId]);

    if (!count) {
        return null;
    }

    return (
        <span className="shrink-0 text-xs text-[#000000]/50">
            {t('geo_sub_locations_count', { count })}
        </span>
    );
}

function GeoLocationListRow({
    value,
    levelLabel,
    showLevelLabel,
    hasChildLevel,
    childLevelIds,
    isChecked,
    onDrillDown,
    onToggle,
}: {
    value: GeoLevelValue;
    levelLabel?: string;
    showLevelLabel: boolean;
    hasChildLevel: boolean;
    childLevelIds: string[];
    isChecked: boolean;
    onDrillDown: () => void;
    onToggle: (checked: boolean) => void;
}) {
    const label = value.level_value_mnemonic || value.level_value_id;

    return (
        <div className="flex items-center border-b border-[#ED7C22]/10 px-5 hover:bg-[#F3F1E4]/30">
            <button
                type="button"
                onClick={() => {
                    if (hasChildLevel) onDrillDown();
                }}
                className={`flex min-w-0 flex-1 items-center gap-2 py-3 text-left text-sm ${
                    hasChildLevel
                        ? 'font-medium text-[#000000] hover:text-[#ED7C22]'
                        : 'text-[#000000]'
                }`}
            >
                <ChevronRight
                    size={14}
                    className={`shrink-0 text-[#000000]/40 ${hasChildLevel ? '' : 'invisible'}`}
                />
                <span className="min-w-0 truncate">
                    {label}
                    {showLevelLabel && levelLabel ? (
                        <span className="ml-2 font-normal text-[#000000]/45">{levelLabel}</span>
                    ) : null}
                </span>
                {hasChildLevel ? (
                    <GeoChildCountBadge
                        childLevelIds={childLevelIds}
                        parentLevelValueId={value.level_value_id}
                    />
                ) : null}
            </button>
            <label className="flex shrink-0 cursor-pointer items-center py-3 pl-3">
                <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={(event) => onToggle(event.target.checked)}
                    className="h-4 w-4 accent-[#ED7C22]"
                />
            </label>
        </div>
    );
}

function buildHierarchyRecord(
    navigationStack: BreadcrumbItem[],
    currentLevel: GeoLevel,
    value: GeoLevelValue,
): GeoHierarchyRecord {
    const record: GeoHierarchyRecord = navigationStack.map((item) => ({
        level: item.levelMnemonic,
        level_value_id: item.levelValueId,
        level_value_mnemonic: item.levelValueMnemonic,
    }));

    record.push({
        level: currentLevel.level_mnemonic,
        level_value_id: value.level_value_id,
        level_value_mnemonic: value.level_value_mnemonic || value.level_value_id,
    });

    return record;
}

export default function GeoLocationPickerModal({
    geoLevels,
    onClose,
    onConfirm,
}: GeoLocationPickerModalProps) {
    const t = useTranslations();
    const orderedLevels = useMemo(() => orderGeoLevelsByHierarchy(geoLevels), [geoLevels]);
    const roots = useMemo(() => getRootLevels(orderedLevels), [orderedLevels]);

    const [navigationStack, setNavigationStack] = useState<BreadcrumbItem[]>([]);
    const [filterText, setFilterText] = useState('');
    const [pendingSelections, setPendingSelections] = useState<Map<string, GeoLocationSelection>>(
        () => new Map(),
    );

    const currentParent = navigationStack[navigationStack.length - 1];
    const listingLevels = currentParent
        ? getChildLevels(orderedLevels, currentParent.levelId)
        : roots;
    const listingLevelIds = listingLevels.map((level) => level.level_id).join('|');
    const parentLevelValueId = currentParent?.levelValueId ?? '';
    const listingTitle = listingLevels.map((level) => level.level_mnemonic).join(' · ');

    const [allGeoLevelValues, setAllGeoLevelValues] = useState<GeoLevelValue[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!listingLevelIds) {
            setAllGeoLevelValues([]);
            setLoading(false);
            return;
        }

        let cancelled = false;
        setLoading(true);
        Promise.all(
            listingLevelIds.split('|').map((levelId) =>
                fetchGeoLevelValues(levelId, parentLevelValueId),
            ),
        )
            .then((groups) => {
                if (!cancelled) setAllGeoLevelValues(groups.flat());
            })
            .finally(() => {
                if (!cancelled) setLoading(false);
            });

        return () => {
            cancelled = true;
        };
    }, [listingLevelIds, parentLevelValueId]);

    const filteredValues = useMemo(() => {
        const query = filterText.trim().toLowerCase();
        if (!query) return allGeoLevelValues;
        return allGeoLevelValues.filter((value) => {
            const label = value.level_value_mnemonic || value.level_value_id;
            return label.toLowerCase().includes(query);
        });
    }, [allGeoLevelValues, filterText]);

    const rootLabel = orderedLevels[0]?.level_mnemonic || t('geo_location_root');

    const toggleSelection = (value: GeoLevelValue, checked: boolean) => {
        const valueLevel = orderedLevels.find((level) => level.level_id === value.level_id);
        if (!valueLevel) return;

        const hierarchy = buildHierarchyRecord(navigationStack, valueLevel, value);
        const selection = selectionFromHierarchy(hierarchy);
        const key = geoHierarchyKey(hierarchy);

        setPendingSelections((prev) => {
            const next = new Map(prev);
            if (checked) {
                next.set(key, selection);
            } else {
                next.delete(key);
            }
            return next;
        });
    };

    const drillDown = (value: GeoLevelValue) => {
        if (getChildLevels(orderedLevels, value.level_id).length === 0) return;

        const label = value.level_value_mnemonic || value.level_value_id;
        setNavigationStack((prev) => [
            ...prev,
            {
                levelId: value.level_id,
                levelMnemonic:
                    orderedLevels.find((level) => level.level_id === value.level_id)
                        ?.level_mnemonic || value.level_id,
                levelValueId: value.level_value_id,
                levelValueMnemonic: value.level_value_mnemonic || value.level_value_id,
                label,
            },
        ]);
        setFilterText('');
    };

    const navigateTo = (index: number) => {
        setNavigationStack((prev) => (index < 0 ? [] : prev.slice(0, index + 1)));
        setFilterText('');
    };

    const handleConfirm = () => {
        onConfirm(Array.from(pendingSelections.values()));
        onClose();
    };

    if (!orderedLevels.length) {
        return (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#000000]/80 p-6">
                <div className="w-full max-w-lg rounded-[10px] bg-[#FFFFFF] p-6">
                    <p className="text-[#000000]/70">{t('no_geo_levels_for_filter_fields')}</p>
                    <button
                        type="button"
                        onClick={onClose}
                        className="mt-4 rounded-[10px] bg-[#E1E1E1] px-4 py-2 text-sm font-semibold"
                    >
                        {t('close')}
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#000000]/80 p-6">
            <div className="flex max-h-[85vh] w-full max-w-xl flex-col overflow-hidden rounded-[10px] border border-[#ED7C22]/30 bg-[#FFFFFF] shadow-lg">
                <div className="flex items-center justify-between border-b border-[#ED7C22]/20 px-5 py-4">
                    <h3 className="text-lg font-semibold text-[#000000]">
                        {t('select_administrative_location')}
                    </h3>
                    <button
                        type="button"
                        onClick={onClose}
                        className="rounded-[8px] p-1 text-[#000000]/60 hover:bg-[#F3F1E4] hover:text-[#000000]"
                        aria-label={t('close')}
                    >
                        <X size={20} />
                    </button>
                </div>

                <div className="flex min-h-[40px] flex-wrap items-center gap-1 border-b border-[#ED7C22]/20 bg-[#F3F1E4]/40 px-5 py-2 text-sm">
                    <button
                        type="button"
                        onClick={() => navigateTo(-1)}
                        className={`rounded px-1.5 py-0.5 ${
                            navigationStack.length === 0
                                ? 'font-medium text-[#000000]'
                                : 'text-[#ED7C22] hover:bg-[#ED7C22]/10'
                        }`}
                    >
                        {rootLabel}
                    </button>
                    {navigationStack.map((item, index) => (
                        <span key={`${item.levelValueId}-${index}`} className="flex items-center gap-1">
                            <ChevronRight size={14} className="text-[#000000]/40" />
                            <button
                                type="button"
                                onClick={() => navigateTo(index)}
                                className={`rounded px-1.5 py-0.5 ${
                                    index === navigationStack.length - 1
                                        ? 'font-medium text-[#000000]'
                                        : 'text-[#ED7C22] hover:bg-[#ED7C22]/10'
                                }`}
                            >
                                {item.label}
                            </button>
                        </span>
                    ))}
                </div>

                <div className="border-b border-[#ED7C22]/80 bg-[#F3F1E4] px-5 py-2 text-xs text-[#000000]">
                    {listingTitle
                        ? `${listingTitle}. ${t('geo_location_picker_hint')}`
                        : t('geo_location_picker_hint')}
                </div>

                <div className="border-b border-[#ED7C22]/20 px-5 py-3">
                    <div className="relative">
                        <Search
                            size={16}
                            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[#000000]/40"
                        />
                        <input
                            type="text"
                            value={filterText}
                            onChange={(event) => setFilterText(event.target.value)}
                            placeholder={t('filter_geo_locations')}
                            className="w-full rounded-[10px] border border-[#ED7C22] bg-[#FFFFFF] py-2 pl-9 pr-3 text-sm outline-none focus:border-[#ED7C22]"
                        />
                    </div>
                </div>

                <div className="min-h-[220px] max-h-[360px] flex-1 overflow-y-auto">
                    {loading ? (
                        <p className="px-5 py-8 text-center text-sm text-[#000000]/50">
                            {t('filter_loading')}
                        </p>
                    ) : filteredValues.length === 0 ? (
                        <p className="px-5 py-8 text-center text-sm text-[#000000]/50">
                            {t('no_geo_locations_found')}
                        </p>
                    ) : (
                        filteredValues.map((value) => {
                            const valueLevel = orderedLevels.find(
                                (level) => level.level_id === value.level_id,
                            );
                            if (!valueLevel) return null;

                            const hierarchy = buildHierarchyRecord(
                                navigationStack,
                                valueLevel,
                                value,
                            );
                            const key = geoHierarchyKey(hierarchy);
                            const childLevels = getChildLevels(orderedLevels, value.level_id);

                            return (
                                <GeoLocationListRow
                                    key={value.level_value_id}
                                    value={value}
                                    levelLabel={valueLevel.level_mnemonic}
                                    showLevelLabel={listingLevels.length > 1}
                                    hasChildLevel={childLevels.length > 0}
                                    childLevelIds={childLevels.map((level) => level.level_id)}
                                    isChecked={pendingSelections.has(key)}
                                    onDrillDown={() => drillDown(value)}
                                    onToggle={(checked) => toggleSelection(value, checked)}
                                />
                            );
                        })
                    )}
                </div>

                <div className="flex items-center justify-between border-t border-[#ED7C22]/20 px-5 py-3">
                    <span className="text-sm font-medium text-[#ED7C22]">
                        {t('geo_locations_selected_count', { count: pendingSelections.size })}
                    </span>
                    <div className="flex gap-2">
                        <button
                            type="button"
                            onClick={onClose}
                            className="rounded-[10px] border border-[#ED7C22]/40 bg-[#FFFFFF] px-4 py-2 text-sm font-semibold text-[#000000]/70"
                        >
                            {t('cancel')}
                        </button>
                        <button
                            type="button"
                            onClick={handleConfirm}
                            disabled={pendingSelections.size === 0}
                            className="rounded-[10px] bg-[#000000] px-4 py-2 text-sm font-semibold text-[#FFFFFF] disabled:opacity-50"
                        >
                            {t('select')}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

export type { GeoLocationSelection } from '../types/geoLocationTypes';
