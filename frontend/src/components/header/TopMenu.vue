<template>
  <div class="w3-bar teal">
    <router-link to="/drive-selection" class="w3-bar-item w3-button">Подбор электропривода</router-link>
    <router-link to="/cable-gland-edit" class="w3-bar-item w3-button">Подбор кабельного ввода</router-link>
    <router-link to="/client-requests" class="w3-bar-item w3-button">Запросы клиентов</router-link>

    <div class="w3-dropdown-hover">
      <button class="w3-button">Редактирование справочников</button>
      <div class="w3-dropdown-content w3-bar-block teal w3-card-4">
        <router-link to="/drive-data" class="w3-bar-item w3-button">Данные приводов</router-link>
        <router-link to="/ett-decode" class="w3-bar-item w3-button">Расшифровка ЕТТ</router-link>
        <router-link to="/cable-gland-body-material-edit" class="w3-bar-item w3-button">Редактирование материала кабельных вводов</router-link>
        <router-link to="/cable-input-data" class="w3-bar-item w3-button">Данные по кабельным вводам</router-link>
        <router-link to="/adaptation-data" class="w3-bar-item w3-button">Данные по адаптации</router-link>
        <a href="/src/apps/media-library/index.html" class="w3-bar-item w3-button">🖼️ Медиабиблиотека</a>
      </div>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
</style>
