// main.js
import {createApp} from 'vue';


// import store from '../src/services/store.js';
import axiosPlugin from '../src/services/axios.js'
import App from './App.vue';
import router from './router';
import './style.css';
import Router from "./router";
//
// Vue.config.productionTip = false;  // Отключаем подсказки для production
// Vue.config.devtools = true;        // Включаем Vue Devtools

//
// new Vue({
//   store,  // Подключаем хранилище
//   render: h => h(App),
// }).$mount('#app');

const app = createApp(App);
app.use(router);  // Подключаем роутер
// // app.use(store);   // Подключаем Vuex store
app.use(axiosPlugin); // Используем плагин axios
app.mount('#app');

// App.vue
// <template>
//   <div class="app">
//     <Header />
//     <div class="main-layout">
//       <div class="sidebar">
//         <slot name="sidebar" />
//       </div>
//       <div class="content">
//         <router-view />
//       </div>
//     </div>
//   </div>
// </template>
//
// <script>
// import Header from './components/Header.vue';
//
// export default {
//   components: { Header },
// };
// </script>