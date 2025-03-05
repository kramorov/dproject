<template>
  <div>
    <slot v-if="url" :url="url"></slot>
    <p v-else>Загрузка URL...</p>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "GetUrl",
  props: {
    paramName: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      url: null,
      req: null,
      name_str: null,
    };
  },
  watch: {
    paramName: {
      handler: "fetchUrl",
      immediate: true,
    },
  },
  methods: {
    async fetchUrl() {
      const url = `/api/get-url/${this.paramName}/`;
      console.log('URL запроса:', url);
      try {
            const response = await axios.get(url);
        // const response = await axios.get(`/api/get-url/${this.paramName}/`);
        // const response = await axios.get('http://127.0.0.1:8000/api/get-url/mounting-plate-types-list/');

        console.log("Ответ сервера:", response.data); // Лог для проверки ответа
        console.log("Ответ сервера url:", response.data.url); // Лог для проверки ответа
        console.log("Был отправлен запрос:", response.data.req); // Лог для проверки ответа
        console.log("Было передано имя:", response.data.name_str); // Лог для проверки ответа
        if (response.data && response.data.url) {
          this.url = response.data.url;
        } else {
          console.error("URL отсутствует в ответе сервера.");
        }
      } catch (error) {
        console.error("Ошибка при запросе URL:", error);
      }
    },
  },
};
</script>
