import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axiosPlugin from './services/axios.js'
import '@/shared/themes/default.css'
const app = createApp(App); app.use(router); app.use(axiosPlugin); app.mount('#app')
