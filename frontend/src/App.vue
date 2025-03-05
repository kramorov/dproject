<template>
  <div class="app">
    <AppLayout>
      <template #header><Header /></template>
      <template #main>
        <div class="main-layout">
          <main class="content">
            <router-view /> <!-- Здесь будет отображаться HomePage -->
    <!--        <router-view>-->
    <!--          &lt;!&ndash; Центральное содержимое страниц будет отображаться здесь через Vue Router &ndash;&gt;-->
    <!--        </router-view>-->
          </main>
        </div>
      </template>
<!--      <template #footer><Header /></template>-->
    </AppLayout>
  </div>
</template>

<script>
import Header from './components/header/Header.vue';
import AppLayout from "./components/AppLayout.vue";

export default {
  name: 'App',
  components: { Header,AppLayout },

};
</script>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
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
</style>
