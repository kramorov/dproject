<template>
  <div class="w3-container">
    <h2>Типы запросов клиентов</h2>
    <button @click="showCreateForm" class="w3-button w3-blue">Добавить тип запроса</button>
    <ul class="w3-ul">
      <li v-for="type in types" :key="type.id" class="w3-bar">
        <span class="w3-bar-item">{{ type.symbolic_code }}</span>
        <button @click="editType(type)" class="w3-button w3-green">Редактировать</button>
        <button @click="deleteType(type.id)" class="w3-button w3-red">Удалить</button>
      </li>
    </ul>

    <div v-if="isFormVisible" class="w3-modal" style="display:block">
      <div class="w3-modal-content">
        <header class="w3-container w3-blue">
          <span @click="hideForm" class="w3-button w3-display-topright">&times;</span>
          <h2>{{ formTitle }}</h2>
        </header>
        <div class="w3-container">
          <input v-model="currentType.symbolic_code" placeholder="Название типа запроса" class="w3-input">
          <label><input type="checkbox" v-model="currentType.need_valve_selection"> Подбор арматуры</label>
          <label><input type="checkbox" v-model="currentType.need_electric_actuator_selection"> Подбор электропривода</label>
          <label><input type="checkbox" v-model="currentType.need_pneumatic_actuator_selection"> Подбор пневмопривода</label>
        </div>
        <footer class="w3-container w3-blue">
          <button @click="saveType" class="w3-button w3-green">Сохранить</button>
        </footer>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      types: [],
      currentType: { id: null, symbolic_code: '', need_valve_selection: false, need_electric_actuator_selection: false, need_pneumatic_actuator_selection: false },
      isFormVisible: false,
      isEditing: false
    };
  },
  computed: {
    formTitle() {
      return this.isEditing ? 'Редактировать тип запроса' : 'Добавить тип запроса';
    }
  },
  methods: {
    showCreateForm() {
      this.isEditing = false;
      this.currentType = { id: null, symbolic_code: '', need_valve_selection: false, need_electric_actuator_selection: false, need_pneumatic_actuator_selection: false };
      this.isFormVisible = true;
    },
    editType(type) {
      this.isEditing = true;
      this.currentType = { ...type };
      this.isFormVisible = true;
    },
    hideForm() {
      this.isFormVisible = false;
    },
    saveType() {
      // Здесь должен быть вызов API для сохранения или обновления типа запроса
      this.hideForm();
      this.fetchTypes();
    },
    deleteType(id) {
      // Здесь должен быть вызов API для удаления типа запроса
      this.fetchTypes();
    },
    fetchTypes() {
      // Здесь должен быть вызов API для получения списка типов запросов
    }
  },
  mounted() {
    this.fetchTypes();
  }
};
</script>