import axios from 'axios';
import {API_URL} from "../../config/api";
import {DictionaryCache, DictionaryConfig, ModelFieldCacheItem, ModelFieldStructure} from "./models";
// import {API_URL} from '@/config/api.js'



// 2. Конфигурация справочников
const DICTIONARY_CONFIG: Record<string, DictionaryConfig> = {
    'ClientRequestsType': {
        url: '/api/core/?model=client_requests.ClientRequestsType',
        ttl: 300 * 60 * 1000 // 300 минут
    },
    'ClientRequestsStatus': {
        url: '/api/core/?model=client_requests.ClientRequestsStatus',
        ttl: 60 * 60 * 1000 // 1 час
    },
    'Company': {
        url: '/api/core/?model=clients.Company',
        ttl: 60 * 60 * 1000 // 1 час
    },
    'CompanyPerson': {
        url: '/api/core/?model=clients.CompanyPerson',
        ttl: 60 * 60 * 1000 // 1 час
    },
    'ClientRequests': {
        url: '/api/core/?model=client_requests.ClientRequests',
        ttl: 24 * 60 * 60 * 1000 // 24 часа
    },
    'ClientRequestItem': {
        url: '/api/core/?model=client_requests.ClientRequestItem',
        ttl: 24 * 60 * 60 * 1000 // 24 часа
    },
    'ElectricActuatorRequirement': {
        url: '/api/core/?model=client_requests.ElectricActuatorRequirement',
        ttl: 24 * 60 * 60 * 1000 // 24 часа
    },
    'ValveRequirement': {
        url: '/api/core/?model=client_requests.ValveRequirement',
        ttl: 24 * 60 * 60 * 1000 // 24 часа
    },
    'ValveSelection': {
        url: '/api/core/?model=client_requests.ValveSelection',
        ttl: 24 * 60 * 60 * 1000 // 24 часа
    }
};

// 3. Инициализируем кэш с правильным типом
const dictionaryCache: Record<string, DictionaryCache> = {};
const modelStructureCache = new Map<string, ModelFieldCacheItem>();

export const DictionaryStore = {
    async getDictionaryItemById(dictionaryName: string, itemId: number | string, forceUpdate = false) {
        if (itemId === undefined) {
            return []
        }
        const config = DICTIONARY_CONFIG[dictionaryName];
        if (!config) {
            console.warn(`Dictionary ${dictionaryName} not found in config`);
            return [];
        }
        try {
            const response = await axios.get(`${API_URL}${DICTIONARY_CONFIG[dictionaryName].url}&id=${itemId}`);
            // console.log('response.data',response.data)
            // let response_data=response.data
            // console.log('response_data',response_data)
            return response.data;
        } catch (error) {
            console.error(`Error loading dictionary ${dictionaryName}:`, error);
            return [];
        }
    },
    async getDictionaryStructure(name: string, forceUpdate = false) {
        if (!DICTIONARY_CONFIG[name]) {
            console.warn(`Dictionary ${name} not found in config`);
            return undefined;
        }
        // Проверяем актуальность кэша
       const cachedItem = modelStructureCache.get(name);
        if (cachedItem && !forceUpdate) {
            return cachedItem;
        }

        try {
            const response = await axios.get(`${API_URL}${DICTIONARY_CONFIG[name].url}&action=form-structure`)
            // Создаем объект с начальными значениями
            const fields: ModelFieldStructure[] = response.data;
            const newCacheItem: ModelFieldCacheItem = {
                fields,
                fieldMap: new Map(fields.map(f => [f.name, f])),
                emptyObj: fields.reduce((acc, field) => {
                    acc[field.name] = field.name === 'id' ? null : (field.type === 'Relation' ? null : '');
                    return acc;
                }, {} as Record<string, any>),
                lastUpdated: Date.now()
            };

            modelStructureCache.set(name, newCacheItem);
            // console.log(`modelStructureCache.set .${name}.`);
            modelStructureCache.set(name, newCacheItem);
            return newCacheItem;
        } catch (error) {
            console.error(`Error loading dictionary structure ${name}:`, error);
            return undefined;
        }
    },
    async getModelStructureField(modelName: string, fieldName: string): Promise<ModelFieldStructure | undefined> {
        try {
            // Получаем структуру из кэша или загружаем
            let foundStructure = modelStructureCache.get(modelName);
            if (!foundStructure) {
                foundStructure = await this.getDictionaryStructure(modelName);
                if (!foundStructure) {
                    console.warn(`Structure for ${modelName} not found or couldn't be loaded`);
                    return undefined;
                }
            }

            // 2. Проверяем наличие fieldMap и его содержимое
            if (!foundStructure.fieldMap || foundStructure.fieldMap.size === 0) {
                console.warn(`FieldMap is empty for ${modelName}`);
                return undefined;
        }
            // console.log(`getModelStructureFieldSync modelName:${modelName}, fieldName:${fieldName} `);
            // console.log(`modelStructureCache)`, modelStructureCache);
            // console.log(`modelStructureCache.has(modelName))`, modelStructureCache.has('ClientRequestItem'));
            // // 'ClientRequestItem'
            // console.log(`foundStructure`, foundStructure);
            // console.log(`foundStructure.fieldMap.get(fieldName)`, foundStructure.fieldMap.get(fieldName));
            // Возвращаем поле
            // 3. Ищем конкретное поле
            const foundField = foundStructure.fieldMap.get(fieldName);
            if (!foundField) {
                console.warn(`Field ${fieldName} not found in ${modelName}`);
                return undefined;
            }

            return foundField;
        } catch (error) {
            console.error(`Error getting field ${fieldName} from ${modelName}:`, error);
            return undefined;
        }
    },
    async getDictionary(name: string, forceUpdate = false) {
        const config = DICTIONARY_CONFIG[name];
        if (!config) {
            console.warn(`Dictionary ${name} not found in config`);
            return [];
        }

        const cachedData = dictionaryCache[name];

        // Проверяем актуальность кэша
        if (cachedData && !forceUpdate &&
            (Date.now() - cachedData.lastUpdated) < config.ttl) {
            return cachedData.data;
        }

        try {
            const response = await axios.get(`${API_URL}${DICTIONARY_CONFIG[name].url}`)
            dictionaryCache[name] = {
                data: response.data,
                lastUpdated: Date.now()
            };
            return response.data;
        } catch (error) {
            console.error(`Error loading dictionary ${name}:`, error);
            return cachedData?.data || [];
        }
    },
    async getDictionaryAsAList(name: string, depth = 0) {
        const config = DICTIONARY_CONFIG[name];
        // console.log(`depth=`,depth);
        if (!config) {
            console.warn(`Dictionary ${name} not found in config`);
            return [];
        }
        try {
            const response = await axios.get(`${API_URL}${DICTIONARY_CONFIG[name].url}&depth=${depth}`)
            return response.data;
        } catch (error) {
            console.error(`Error loading dictionary ${name}:`, error);
            return [];
        }
    },

    async preloadAllDictionaries() {
        const dictionaryNames = Object.keys(DICTIONARY_CONFIG);

        // console.log('Starting preload of all dictionaries:');
        dictionaryNames.forEach(name => {
            const url = `${API_URL}${DICTIONARY_CONFIG[name].url}`;
            // console.log(`- ${name}: ${url}`);
        });

        await Promise.all(dictionaryNames.map(name => {
            const url = `${API_URL}${DICTIONARY_CONFIG[name].url}`;
            // console.log(`Fetching ${name} from ${url}`);
            return this.getDictionary(name);
        }));
        await Promise.all(dictionaryNames.map(name => {
            const url = `${API_URL}${DICTIONARY_CONFIG[name].url}&action=form-structure`;
            return this.getDictionaryStructure(name);
        }));

        // console.log('All dictionaries preloaded');
    },

    forceRefreshDictionary(name: string) {
        return this.getDictionary(name, true);
    },

    getConfig() {
        return DICTIONARY_CONFIG;
    }
};
export const getDictionaryStructure = DictionaryStore.getDictionaryStructure;
export const getModelStructureField = DictionaryStore.getModelStructureField;