// widget/main.js — Точка входа виджета.
// Читает data-key из атрибута скрипта, запрашивает конфиг, монтирует App.
import { createApp } from 'vue'
import App from './App.vue'

// Базовая тема
import '@/shared/themes/default.css'

async function init() {
  const scriptEl = document.currentScript
  const partnerKey = scriptEl?.getAttribute('data-key') || 'default'

  // В будущем: запрос конфига с сервера
  // const config = await fetch(`/api/widget/config/?key=${partnerKey}`).then(r => r.json())
  // const allowedCatalogs = config.catalogs || ['gearbox']

  // Пока жёстко
  const allowedCatalogs = ['gearbox']

  const app = createApp(App, { allowedCatalogs })
  app.mount('#widget-root')
}

init()
