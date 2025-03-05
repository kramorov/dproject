<template>
  <div id="app">
    <!-- Основной контент страницы -->
    <router-view></router-view>

    <!-- Подвал с сообщением о загрузке -->
    <footer v-if="!dataLoaded" class="w3-padding w3-center">
      <p>Загрузка данных...</p>
    </footer>
    <footer v-else class="w3-padding w3-center w3-green">
      <p>Загрузка завершена за {{ loadingTime }} секунд.</p>
    </footer>
  </div>
</template>

<script>
export default {
  computed: {
    dataLoaded() {
      return this.$store.getters.isDataLoaded;
    },
    loadingTime() {
      return this.$store.getters.loadingTime;
    },
  },
  mounted() {
    if (!this.$store.getters.isDataLoaded) {
      this.$store.dispatch('loadGlobalData');
    }
  },
};
</script>

<style scoped>
footer {
  position: fixed;
  bottom: 0;
  width: 100%;
}
</style>

<!--Теперь, когда данные загружены и хранятся в хранилище, вы можете использовать их в любых компонентах, подключая Vuex:-->

<!--<template>-->
<!--  <div class="w3-container">-->
<!--    <h2>Данные</h2>-->
<!--    <ul v-if="globalData">-->
<!--      <li v-for="(item, index) in globalData" :key="index">{{ item.name }}</li>-->
<!--    </ul>-->
<!--    <p v-else>Данные еще не загружены.</p>-->
<!--  </div>-->
<!--</template>-->

<!--<script>-->
<!--export default {-->
<!--  computed: {-->
<!--    globalData() {-->
<!--      return this.$store.getters.globalData;-->
<!--    },-->
<!--  },-->
<!--};-->
<!--</script>-->
