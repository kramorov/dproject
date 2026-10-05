// src/services/axios.js
// ЛЕГАСИ-плагин. Реальный API-клиент проекта — src/shared/api.js (свой инстанс axios + CSRF).
// НЕ мутируем глобальные defaults axios: раньше здесь ставилась заглушка
//   axios.defaults.headers.common['Authorization'] = 'Bearer your_token_here'
// и попадала во все запросы.
import axios from 'axios'

export default {
  install: (app) => {
    // $axios в коде не используется; оставлен для обратной совместимости.
    app.config.globalProperties.$axios = axios
  },
}
