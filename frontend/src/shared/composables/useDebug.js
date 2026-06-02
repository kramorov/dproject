// shared/composables/useDebug.js
// Временная отладка — убрать после завершения.
import { reactive } from 'vue'

const state = reactive({
  /** Установить из дочернего компонента: название страницы/режима */
  page: '',
})

export function useDebug() {
  return state
}
