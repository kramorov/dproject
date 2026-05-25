// src/apps/gearbox-catalog/main.js
import { createApp } from 'vue'
import App from './App.vue'

// Базовая тема — всегда. Партнёр может переопределить переменные
// своим CSS или подключить themes/dark.css / themes/minimal.css
import '@/shared/themes/default.css'

createApp(App).mount('#gearbox-app')
