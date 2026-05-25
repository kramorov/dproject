// shared/stores/catalogMeta.js
// Реактивное хранилище метаданных полей для всех типов каталога.
// Грузит /api/{model}/meta/ один раз, кэширует.
import { reactive } from 'vue'
import api from '@/shared/api'

const state = reactive({
  /** { gearbox: { field_key: {label, group, unit, type, order} }, pa: {...} } */
  meta: {},
  loaded: {},
  loading: {},
})

export function useCatalogMeta() {
  /**
   * Загрузить метаданные для модели (gearBox, pneumaticActuator, ...).
   * @param {string} model - имя модели (gearBox, etc.)
   * @returns {Promise<object>}
   */
  async function loadMeta(model) {
    if (state.loaded[model]) return state.meta[model]
    if (state.loading[model]) {
      // Ждём пока загрузится
      return new Promise(resolve => {
        const check = setInterval(() => {
          if (state.loaded[model]) {
            clearInterval(check)
            resolve(state.meta[model])
          }
        }, 100)
      })
    }

    state.loading[model] = true
    try {
      const r = await api.get(`/${model}/meta/`)
      state.meta[model] = r.data || {}
      state.loaded[model] = true
      return state.meta[model]
    } catch (e) {
      console.error(`[catalogMeta] Failed to load meta for ${model}`, e)
      state.meta[model] = {}
      state.loaded[model] = true
      return {}
    } finally {
      state.loading[model] = false
    }
  }

  /**
   * Получить уже загруженные метаданные (без запроса).
   */
  function getMeta(model) {
    return state.meta[model] || {}
  }

  return { loadMeta, getMeta }
}
