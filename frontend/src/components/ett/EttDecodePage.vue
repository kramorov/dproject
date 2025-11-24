<template>
  <div class="w3-container">
    <!-- Текстовое поле ввода -->
    <input
      type="text"
      v-model="inputText"
      placeholder="Введите текст"
      class="w3-input w3-border w3-margin-bottom"
    />

    <!-- Кнопка "Отправить" -->
    <button @click="sendRequest" class="w3-button w3-blue w3-margin-bottom">Отправить</button>

    <!-- Поле для вывода ответа -->
    <div class="w3-container w3-margin-top">
      <p v-if="response" class="w3-text-green">Ответ{{ response }}</p>
      <p v-if="error" class="w3-text-red">Ошибка{{ error }}</p>

      <div class="w3-modal-content w3-animate-zoom">

        <!-- Таблица параметров -->
        <div class="w3-container">
          <div class="w3-responsive">
            <table class="w3-table w3-striped w3-border w3-text-black">
              <thead>
                <tr>
                  <th>Параметр</th>
                  <th>Значение</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(param, index) in desc_table" :key="index">
                  <td>{{ param.param_name }}</td>
                  <td>{{ param.param_value }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
export default {
  data() {
    return {
      inputText: "",  // Хранит текст из поля ввода
      response: null, // Хранит полученный ответ от сервера
      error: null,    // Хранит ошибку, если она возникла
      desc_table : []
    };
  },
  methods: {
    async sendRequest() {
      try {
        // Очистка старого ответа и ошибки перед отправкой нового запроса
        this.response = null;
        this.error = null;

        // Отправка POST-запроса с текстом
        const response = await this.$axios.post('/ett/decode/', {
          input_string: this.inputText,
        });

        // Если запрос успешен, сохраняем ответ
        // console.log(response.data);
        // console.log(this.response.desc_table);
        this.response = response.data.message; // Предположим, что ответ имеет поле message
        this.desc_table = response.data.desc_table;
      } catch (err) {
        // Если произошла ошибка, сохраняем текст ошибки
        // console.log(err.response);
        this.error = err.response ? err.response.data.message : 'Ошибка сети';
      }
    },
  },
};
</script>

<style scoped>
/* Дополнительные стили, если нужно */
</style>
