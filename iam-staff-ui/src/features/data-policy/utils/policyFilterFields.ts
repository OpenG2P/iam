export type PolicyFilterField = {
    id: string;
    label: string;
    dataType: string;
};

export function fromRegisterFields(fields: any[]): PolicyFilterField[] {
    return fields.map((field) => ({
        id: field.field_name,
        label: `${field.field_name} (${field.data_type})`,
        dataType: field.data_type,
    }));
}

export function fromAttributes(attributes: any[]): PolicyFilterField[] {
    return attributes.map((attribute) => ({
        id: attribute.attribute_code,
        label: attribute.attribute_display || attribute.attribute_code,
        dataType: 'string',
    }));
}

export function fromGeoLevels(levels: any[]): PolicyFilterField[] {
    return levels.map((level) => ({
        id: level.level_mnemonic,
        label: level.level_mnemonic || level.level_id,
        dataType: 'geo_hierarchy',
    }));
}

export function getPolicyFilterFieldLabel(
    fields: PolicyFilterField[],
    fieldId: string,
): string {
    return fields.find((field) => field.id === fieldId)?.label ?? fieldId;
}
