<template>
  <div class="site-background w3-light-gray">
    <div class="app">
      <AppLayout>
        <template #header>
          <Header />
        </template>
        <template #main>
          <div class="main-layout">
            <main class="content">
              <!-- Индикатор загрузки -->
              <div v-if="dataStore.isLoading" class="loading-overlay">
                <div class="loading-spinner"></div>
                <p>{{ loadingMessage }}</p>
              </div>

              <!-- Сообщение об ошибке -->
              <div v-else-if="dataStore.error" class="error-message">
                {{ loadingMessage }}
                <button @click="dataStore.fetchInitialData">Повторить</button>
              </div>
              <!-- Основной контент -->

              <!-- Основной контент -->
              <router-view v-else />
            </main>
          </div>
        </template>
      </AppLayout>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import Header from './components/header/Header.vue';
import AppLayout from "./components/AppLayout.vue";
import {useDataStore} from '@/services/store.js';

// Инициализация хранилища
const dataStore = useDataStore();
const loadingMessage = ref('Загрузка данных...')
// Запускаем загрузку при монтировании
onMounted(async () => {
  await dataStore.fetchInitialData()
})
// Можно следить за изменениями статуса загрузки
watch(() => dataStore.isLoading, (isLoading) => {
  if (!isLoading && dataStore.error) {
    loadingMessage.value = `Ошибка: ${dataStore.error}`
  }
})
</script>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-layout {
  display: flex;
  flex: 1;
}

.content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.site-background {
  min-height: 100vh;
  padding: 20px;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  color: red;
  padding: 20px;
  text-align: center;
}
</style>
