import type { GeoLevel } from '../hooks/useG2pGeoLevels';

export function getRootLevels(levels: GeoLevel[]): GeoLevel[] {
    return levels.filter((level) => !level.parent_level_id);
}

export function getChildLevels(levels: GeoLevel[], parentLevelId: string): GeoLevel[] {
    return levels.filter((level) => level.parent_level_id === parentLevelId);
}

export function orderGeoLevelsByHierarchy(levels: GeoLevel[]): GeoLevel[] {
    const result: GeoLevel[] = [];
    const visited = new Set<string>();

    const walk = (level: GeoLevel) => {
        if (visited.has(level.level_id)) return;
        visited.add(level.level_id);
        result.push(level);
        for (const child of getChildLevels(levels, level.level_id)) {
            walk(child);
        }
    };

    for (const root of getRootLevels(levels)) {
        walk(root);
    }

    return result;
}

export function findGeoLevelByMnemonic(levels: GeoLevel[], mnemonic: string): GeoLevel | undefined {
    return levels.find((level) => level.level_mnemonic === mnemonic);
}
