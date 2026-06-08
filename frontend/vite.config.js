import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        'media-library': resolve(__dirname, 'src/apps/media-library/index.html'),
        'cert-docs': resolve(__dirname, 'src/apps/cert-docs/index.html'),
        'price-catalog': resolve(__dirname, 'src/apps/price-catalog/index.html'),
        'sku-admin': resolve(__dirname, 'src/apps/sku-admin/index.html'),
        'gearbox-catalog': resolve(__dirname, 'src/apps/gearbox-catalog/index.html'),
        'filter-regulator-catalog': resolve(__dirname, 'src/apps/filter-regulator-catalog/index.html'),
        'limit-switch-catalog': resolve(__dirname, 'src/apps/limit-switch-catalog/index.html'),
        'solenoid-valves-catalog': resolve(__dirname, 'src/apps/solenoid-valves-catalog/index.html'),
        'limit-switch-admin': resolve(__dirname, 'src/apps/limit-switch-admin/index.html'),
        'widget': resolve(__dirname, 'src/apps/widget/index.html'),
        'actuator-constructor': resolve(__dirname, 'src/apps/actuator-constructor/index.html'),
      },
    },
  },
})
