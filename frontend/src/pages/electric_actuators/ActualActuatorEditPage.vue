<template>
  <div class="w3-container">
    <h2>Редактирование модели</h2>
    <form @submit.prevent="handleSubmit" class="w3-card-4 w3-padding-large">
      <!-- Название проекта -->
      <div class="w3-row w3-margin-bottom">
        <label for="name" class="w3-label">Название проекта</label>
        <input type="text" id="name" v-model="formData.name" class="w3-input w3-border" required />
      </div>

      <!-- Статус проекта -->
      <div class="w3-row w3-margin-bottom">
        <label for="status" class="w3-label">Статус</label>
        <select v-model="formData.status" id="status" class="w3-select w3-border">
          <option value="Draft">Проект</option>
          <option value="Approved">Утвержден</option>
        </select>
      </div>

      <!-- Базовая модель -->
      <div class="w3-row w3-margin-bottom">
        <label for="actual_model" class="w3-label">Базовая модель</label>
        <select v-model="formData.actual_model" id="actual_model" class="w3-select w3-border">
          <option v-for="model in models" :key="model.id" :value="model.id">{{ model.name }}</option>
        </select>
      </div>

      <!-- Время поворота -->
      <div class="w3-row w3-margin-bottom">
        <label for="actual_time_to_open" class="w3-label">Время поворота</label>
        <input type="number" id="actual_time_to_open" v-model="formData.actual_time_to_open" class="w3-input w3-border" />
      </div>

      <!-- Единица измерения времени поворота -->
      <div class="w3-row w3-margin-bottom">
        <label for="actual_time_to_open_measure_unit" class="w3-label">Единица измерения времени</label>
        <select v-model="formData.actual_time_to_open_measure_unit" id="actual_time_to_open_measure_unit" class="w3-select w3-border">
          <option v-for="unit in timeUnits" :key="unit.id" :value="unit.id">{{ unit.name }}</option>
        </select>
      </div>

      <!-- Скорость -->
      <div class="w3-row w3-margin-bottom">
        <label for="actual_rotations_to_open" class="w3-label">Скорость</label>
        <input type="number" id="actual_rotations_to_open" v-model="formData.actual_rotations_to_open" class="w3-input w3-border" />
      </div>

      <!-- Дополнительные поля с выбором -->
      <div v-for="(field, index) in relatedFields" :key="index" class="w3-row w3-margin-bottom">
        <label :for="field.id" class="w3-label">{{ field.label }}</label>
        <select v-model="formData[field.id]" :id="field.id" class="w3-select w3-border">
          <option v-for="option in field.options" :key="option.id" :value="option.id">{{ option.name }}</option>
        </select>
      </div>

      <!-- Текстовое описание -->
      <div class="w3-row w3-margin-bottom">
        <label for="text_description" class="w3-label">Описание</label>
        <textarea id="text_description" v-model="formData.text_description" class="w3-input w3-border" rows="4"></textarea>
      </div>

      <button type="submit" class="w3-button w3-blue">Сохранить</button>
    </form>
  </div>
</template>

<script>
export default {
  name: "ActualActuatorEditPage.vue",
  data() {
    return {
      formData: {
        name: '',
        status: 'Draft',
        actual_model: null,
        actual_time_to_open: null,
        actual_time_to_open_measure_unit: null,
        actual_rotations_to_open: null,
        text_description: '',
        // Поля с ForeignKey будут заполняться в процессе загрузки данных
      },
      models: [],
      timeUnits: [],
      relatedFields: [
        {
          id: 'actual_stem_shape',
          label: 'Тип отверстия под шток',
          options: [],
        },
        {
          id: 'actual_ip',
          label: 'Степень IP',
          options: [],
        },
        // Пример добавления других полей
      ],
    };
  },
  methods: {
    handleSubmit() {
      console.log('Данные формы:', this.formData);
      // Здесь будет обработка отправки данных на сервер
    },
    loadModels() {
      // Загружаем доступные модели для поля 'actual_model' (например, с API)
      this.models = [
        { id: 1, name: 'Модель 1' },
        { id: 2, name: 'Модель 2' },
        // и т.д.
      ];
    },
    loadTimeUnits() {
      // Загружаем доступные единицы измерения времени (например, с API)
      this.timeUnits = [
        { id: 1, name: 'Секунды' },
        { id: 2, name: 'Минуты' },
        // и т.д.
      ];
    },
    loadRelatedFields() {
      // Загружаем данные для других полей с ForeignKey
      this.relatedFields[0].options = [
        { id: 1, name: 'Тип 1' },
        { id: 2, name: 'Тип 2' },
      ];
      // Заполняем другие поля по мере необходимости
    },
  },
  mounted() {
    this.loadModels();
    this.loadTimeUnits();
    this.loadRelatedFields();
  },
};
</script>

<style scoped>
.w3-label {
  font-weight: bold;
}
.w3-button {
  margin-top: 20px;
}
</style>


<