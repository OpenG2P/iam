'use client';

import { useMemo } from 'react';
import { useTranslations } from 'next-intl';
import { useGeoLevelValues, getGeoLevelValueLabel } from '../hooks/useGeoLevelValues';
import FilterSelect from './FilterSelect';
import {
    type ConditionOperator,
    usesMultiValue,
    usesNoValue,
} from '../utils/policyFilterExpression';

interface PolicyConditionValueInputProps {
    policyTarget: string;
    fieldId: string;
    operator: ConditionOperator;
    valueInput: string;
    onChange: (valueInput: string) => void;
    disabled?: boolean;
}

function GeoValueInput({
    fieldId,
    operator,
    valueInput,
    onChange,
    disabled,
}: {
    fieldId: string;
    operator: ConditionOperator;
    valueInput: string;
    onChange: (valueInput: string) => void;
    disabled?: boolean;
}) {
    const t = useTranslations();
    const { allGeoLevelValues, loading } = useGeoLevelValues(fieldId);
    const options = allGeoLevelValues.map((value) => ({
        label: getGeoLevelValueLabel(value),
        value: value.level_value_id,
    }));
    const multiValue = usesMultiValue(operator);

    if (multiValue) {
        const selected = useMemo(
            () =>
                valueInput
                    .split(',')
                    .map((part) => part.trim())
                    .filter(Boolean),
            [valueInput],
        );

        return (
            <select
                multiple
                value={selected}
                onChange={(event) => {
                    const values = Array.from(event.target.selectedOptions).map(
                        (option) => option.value,
                    );
                    onChange(values.join(', '));
                }}
                disabled={disabled || loading}
                className="min-h-[42px] w-full border border-[#ED7C22] rounded-[10px] px-4 py-2 text-[16px] bg-[#FFFFFF] outline-none focus:outline-none focus:ring-0 focus-visible:ring-0 focus:border-[#ED7C22] disabled:opacity-50 disabled:cursor-not-allowed"
            >
                {!options.length && (
                    <option value="" disabled>
                        {loading ? 'Loading...' : t('select_geo_value')}
                    </option>
                )}
                {options.map((option) => (
                    <option key={option.value} value={option.value}>
                        {option.label}
                    </option>
                ))}
            </select>
        );
    }

    return (
        <FilterSelect
            options={options}
            value={valueInput}
            onChange={onChange}
            loading={loading}
            disabled={disabled || !fieldId}
            placeholder={t('select_geo_value')}
        />
    );
}

function PlainValueInput({
    operator,
    valueInput,
    onChange,
    disabled,
}: {
    operator: ConditionOperator;
    valueInput: string;
    onChange: (valueInput: string) => void;
    disabled?: boolean;
}) {
    const t = useTranslations();
    const multiValue = usesMultiValue(operator);

    return (
        <input
            type="text"
            value={valueInput}
            onChange={(event) => onChange(event.target.value)}
            placeholder={
                multiValue ? t('filter_values_placeholder') : t('filter_value_placeholder')
            }
            disabled={disabled}
            className="w-full border border-[#ED7C22] rounded-[10px] px-4 py-2 text-[16px] bg-[#FFFFFF] outline-none focus:outline-none focus:ring-0 focus-visible:ring-0 focus:border-[#ED7C22] disabled:opacity-50 disabled:cursor-not-allowed"
        />
    );
}

export default function PolicyConditionValueInput({
    policyTarget,
    fieldId,
    operator,
    valueInput,
    onChange,
    disabled,
}: PolicyConditionValueInputProps) {
    if (usesNoValue(operator)) {
        return <span />;
    }

    if (policyTarget === 'GEO') {
        return (
            <GeoValueInput
                fieldId={fieldId}
                operator={operator}
                valueInput={valueInput}
                onChange={onChange}
                disabled={disabled}
            />
        );
    }

    return (
        <PlainValueInput
            operator={operator}
            valueInput={valueInput}
            onChange={onChange}
            disabled={disabled}
        />
    );
}
