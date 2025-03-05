<template>
  <div>
    <!-- Кнопка для открытия модального окна -->
    <button @click="openModal" class="w3-button w3-blue">Показать параметры</button>

    <!-- Модальное окно -->
    <div v-if="isModalOpen" class="w3-modal" @click.self="closeModal">
      <div class="w3-modal-content w3-animate-zoom">
        <!-- Заголовок окна -->
        <header class="w3-container w3-blue">
          <span @click="closeModal" class="w3-button w3-display-topright">&times;</span>
          <h2>{{ modalTitle }}</h2>
        </header>

        <!-- Таблица параметров -->
        <div class="w3-container">
          <table class="w3-table w3-bordered">
            <thead>
              <tr>
                <th>Параметр</th>
                <th>Значение</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(param, index) in paramTable" :key="index">
                <td>{{ param.param_name }}</td>
                <td>{{ param.param_value }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Кнопка для закрытия окна -->
        <footer class="w3-container w3-center">
          <button @click="closeModal" class="w3-button w3-red">Закрыть</button>
        </footer>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    // Получаем таблицу параметров и заголовок для модального окна
    paramTable: {
      type: Array,
      required: true,
    },
    modalTitle: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      isModalOpen: false,  // Состояние модального окна
    };
  },
  methods: {
    // Открытие модального окна
    openModal() {
      this.isModalOpen = true;
    },
    // Закрытие модального окна
    closeModal() {
      this.isModalOpen = false;
    },
  },
};
</script>

<style scoped>
/* Стили для модального окна */
.w3-modal {
  display: block;
  position: fixed;
  z-index: 1000;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.4);
}

.w3-modal-content {
  position: relative;
  margin: 10% auto;
  padding: 20px;
  width: 50%;
  background-color: white;
  border-radius: 5px;
}

.w3-button {
  cursor: pointer;
}
</style>
