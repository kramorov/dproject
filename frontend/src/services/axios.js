// src/plugins/axios.js
import axios from 'axios';

// Устанавливаем базовый URL
axios.defaults.baseURL = '';

// Настройка axios (например, заголовки, токены и т.д.)
axios.defaults.headers.common['Authorization'] = 'Bearer your_token_here';

export default {
  install: (app) => {
    // Добавляем axios как глобальную переменную
    app.config.globalProperties.$axios = axios;
  },
};
