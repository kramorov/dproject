// main.js
import {createApp} from 'vue';


// import store from '../src/services/store.js';
import axiosPlugin from '../src/services/axios.js'
import App from './App.vue';
import { createPinia } from 'pinia' // Импортируем Pinia
import router from './router';
import './style.css';
import { DictionaryStore } from './services/stores/dictionaryStore.ts';


//
// Vue.config.productionTip = false;  // Отключаем подсказки для production
// Vue.config.devtools = true;        // Включаем Vue Devtools

//
// new Vue({
//   store,  // Подключаем хранилище
//   render: h => h(App),
// }).$mount('#app');

const app = createApp(App);
const pinia = createPinia() // Создаём экземпляр Pinia

app.use(pinia) // Подключаем Pinia к приложению
// Устанавливаем глобальный обработчик ошибок для stores
// При старте приложения Заполняем хранилища при запуске
DictionaryStore.preloadAllDictionaries().then(() => {
  // console.log('All dictionaries loaded');
});

app.use(router);  // Подключаем роутер
// // app.use(store);   // Подключаем Vuex store
app.use(axiosPlugin); // Используем плагин axios
app.mount('#app');

