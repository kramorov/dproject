<script setup>
import HelloWorld from './components/HelloWorld.vue'
</script>

<script>

import MountingPlateTypes from './components/MountingPlates.vue';
import Dictionary from './components/Dictionary.vue';
import GetUrl from './components/GetUrl.vue';
import axios from 'axios';

// axios.defaults.baseURL = 'http://127.0.0.1:8000';

//
// axios.interceptors.request.use((config) => {
//   console.log('Отправляемый запрос:', config);
//   return config;
// }, (error) => {
//   console.error('Ошибка запроса:', error);
//   return Promise.reject(error);
// });


export default {
  name: 'App',

  components: {
    MountingPlateTypes,
    Dictionary,
    GetUrl,
  }
};
</script>

<template>
  <div>
    <div>
      <h1>Пример использования компонента GetUrl</h1>
<!--      <Dictionary />-->
      <GetUrl paramName="mounting-plate-types-list">

        <template #default="{ url }">
          <p>URL для "mounting-plate-types-list": <a :href="url" target="_blank">{{ url }}</a></p>
        </template>
      </GetUrl>
    </div>
<!--    <div id="app">-->
<!--      <MountingPlateTypes />-->
<!--    </div>-->
  </div>
<!--  <HelloWorld msg="Vite + Vue" />-->
</template>

<style scoped>
.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.vue:hover {
  filter: drop-shadow(0 0 2em #42b883aa);
}
</style>
