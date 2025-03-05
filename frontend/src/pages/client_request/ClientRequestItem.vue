<template>
  <div class="w3-container">
    <h2>Строки запроса клиента</h2>
    <button @click="showCreateForm" class="w3-button w3-blue">Добавить строку</button>
    <ul class="w3-ul">
      <li v-for="item in items" :key="item.id" class="w3-bar">
        <span class="w3-bar-item">{{ item.item_no }}: {{ item.request_line_ol }}</span>
        <button @click="editItem(item)" class="w3-button w3-green">Редактировать</button>
        <button @click="deleteItem(item.id)" class="w3-button w3-red">Удалить</button>
      </li>
    </ul>

    <!-- Форма для создания/редактирования строки запроса -->
    <div v-if="isFormVisible" class="w3-modal" style="display:block">
      <div class="w3-modal-content">
        <header class="w3-container w3-blue">
          <span @click="hideForm" class="w3-button w3-display-topright">&times;</span>
          <h2>{{ formTitle }}</h2>
        </header>
        <div class="w3-container">
          <input v-model="currentItem.item_no" type="number" placeholder="Номер строки" class="w3-input">
          <input v-model="currentItem.request_line_number" type="number" placeholder="Номер строки в запросе" class="w3-input">
          <input v-model="currentItem.request_line_ol" placeholder="Идентификатор ОЛ" class="w3-input">
        </div>
        <footer class="w3-container w3-blue">
          <button @click="saveItem" class="w3-button w3-green">Сохранить</button>
        </footer>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      items: [], // Список строк запроса
      currentItem: {
        id: null,
        item_no: 0,
        request_line_number: null,
        request_line_ol: ''
      },
      isFormVisible: false,
      isEditing: false
    };
  },
  computed: {
    formTitle() {
      return this.isEditing ? 'Редактировать строку запроса' : 'Добавить строку запроса';
    }
  },
  methods: {
    showCreateForm() {
      this.isEditing = false;
      this.currentItem = {
        id: null,
        item_no: 0,
        request_line_number: null,
        request_line_ol: ''
      };
      this.isFormVisible = true;
    },
    editItem(item) {
      this.isEditing = true;
      this.currentItem = { ...item };
      this.isFormVisible = true;
    },
    hideForm() {
      this.isFormVisible = false;
    },
    saveItem() {
      // Здесь должен быть вызов API для сохранения или обновления строки запроса
      if (this.isEditing) {
        // Обновить строку
      } else {
        // Создать новую строку
      }
      this.hideForm();
      this.fetchItems();
    },
    deleteItem(id) {
      // Здесь должен быть вызов API для удаления строки запроса
      this.fetchItems();
    },
    fetchItems() {
      // Здесь должен быть вызов API для получения списка строк запроса
    }
  },
  mounted() {
    this.fetchItems();
  }
};
</script>