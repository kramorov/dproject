// 1. Определяем интерфейсы
export interface DictionaryConfig {
    url: string;
    ttl: number;
}

export interface DictionaryCache {
    data: any;
    lastUpdated: number;
}
export interface ModelFieldStructure {
    name: string;
    type: string;
    verbose_name?: string | null;
    help_text?: string | null;
    default?: any;
    related_model?: string | null;
    related_app?: string | null;
    // ... другие известные опциональные поля
    [key: string]: unknown; // Для неизвестных свойств
}

export interface newModelFieldStructure {
    name: string;
    type: string;
    verbose_name?: string | null;
    help_text?: string | null;
    default?: any;
    related_model?: string | null;
    related_app?: string | null;
    // ... другие известные опциональные поля
    [key: string]: unknown; // Для неизвестных свойств
}

export interface ModelFieldCacheItem<T = ModelFieldStructure> {
    fields: T[];
    fieldMap: Map<string, T>;
    emptyObj: Record<string, any>;
    lastUpdated: number;
}