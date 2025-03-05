<template>
  <div id="home-page" class="w3-content">

    <div class="main-layout">
      <main class="content">
        <!-- Центральное содержимое -->
            <h1>Добро пожаловать!</h1>
    <p>Выберите нужный раздел в меню для продолжения работы.</p>
        <p>Центральное содержимое страницы здесь.</p>
      </main>
      <RightSidebar />
    </div>
  </div>
</template>

<script>
import RightSidebar from "../components/RightSidebar.vue";

export default {
  name: "HomePage",
  components: {
    RightSidebar,
  },
};
</script>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.main-layout {
  display: flex;
  flex: 1;
}

.content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  order: 1; /* Контент будет слева */
}
</style>



<!--<template>-->
<!--  <div class="home-page">-->
<!--    <h1>Добро пожаловать!</h1>-->
<!--    <p>Выберите нужный раздел в меню для продолжения работы.</p>-->
<!--  </div>-->
<!--</template>-->

<!--<script>-->
<!--export default {-->
<!--  name: "HomePage",-->
<!--};-->
<!--</script>-->

<!--<style scoped>-->
<!--.home-page {-->
<!--  padding: 20px;-->
<!--  text-align: center;-->
<!--}-->
<!--.home-page h1 {-->
<!--  font-size: 2rem;-->
<!--  color: #333;-->
<!--}-->
<!--.home-page p {-->
<!--  font-size: 1.2rem;-->
<!--  color: #666;-->
<!--}-->
<!--</style>-->
