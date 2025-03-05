<template>
  <div class="cable-gland-form">
    <form @submit.prevent="submitForm">
      <!-- Поле для выбора типа модели -->
      <div class="form-group">
        <label for="itemType">Тип кабельного ввода</label>
        <select v-model="formData.itemType" @change="onItemTypeChange" class="form-control" id="itemType" required>
          <option v-for="type in cableGlandTypes" :key="type.id" :value="type.id">{{ type.name }}</option>
        </select>
      </div>

      <!-- Компонент для редактирования данных в зависимости от типа -->
      <component :is="currentComponent" :formData="formData" :modelLines="modelLines" :threadSizes="threadSizes" :bodyMaterials="bodyMaterials" :exdOptions="exdOptions" :onItemTypeChange="onItemTypeChange" />

      <button type="submit" class="btn btn-primary">Сохранить</button>
    </form>
  </div>
</template>

<script>
import AdapterForm from './CgTypeAdapterForm.vue';
import CableGlandForm from './CgTypeCableGlandForm.vue';
import PlugForm from './CgTypePlugForm.vue';
import GroundRingForm from './CgTypeGroundRingForm.vue';

export default {
  data() {
    return {
      formData: {
        name: '',
        itemType: null,
        modelLine: null,
        cableGlandBodyMaterial: null,
        exd: [],
        threadA: null,
        threadB: null,
        tempMin: null,
        tempMax: null,
        cableDiameterInnerMin: null,
        cableDiameterInnerMax: null,
        cableDiameterOuterMin: null,
        cableDiameterOuterMax: null,
        dnMetalSleeve: null,
        parent: null,
        exd_same_as_model_line: true
      },
      cableGlandTypes: [], // Типы кабельных вводов
      modelLines: [],       // Все модели линий
      threadSizes: [],      // Размеры резьбы
      bodyMaterials: [],    // Материалы корпусов
      exdOptions: [],       // Опции Exd
      currentComponent: null // Текущий компонент для отображения
    };
  },
  created() {
    // Загружаем необходимые данные (например, с API)
    this.loadData();
  },
  methods: {
    async loadData() {
      // Загружаем данные с API (пример)
      const response = await fetch('http://localhost:8000/cg/cable-glands-type/');
      this.cableGlandTypes = await response.json();

      const modelLinesResponse = await fetch('http://localhost:8000/cg/cable-glands-model-lines/');
      this.modelLines = await modelLinesResponse.json();

      const bodyMaterialsResponse = await fetch('http://localhost:8000/cg/cable-glands-materials/');
      this.bodyMaterials = await bodyMaterialsResponse.json();

      const exdOptionsResponse = await fetch('http://localhost:8000/api/params/exd-options/);
      this.exdOptions = await exdOptionsResponse.json();

      const threadSizesResponse = await fetch('http://localhost:8000/api/params/thread-size-types/);
      this.threadSizes = await threadSizesResponse.json();
    },
    onItemTypeChange() {
      // Обновление компонента в зависимости от типа модели
      switch (this.formData.itemType) {
        case 1:
          this.currentComponent = 'CableGlandForm';
          break;
        case 2:
          this.currentComponent = 'AdapterForm';
          break;
        case 3:
          this.currentComponent = 'PlugForm';
          break;
        case 4:
          this.currentComponent = 'GroundRingForm';
          break;
        default:
          this.currentComponent = null;
      }
    },
    async submitForm() {
  // Отправка данных формы
  try {
    const url = this.formData.id
      ? `http://localhost:8000/cg/cable-glands/${this.formData.id}/`  // Если id существует, обновляем конкретную запись
      : '/http://localhost:8000/cg/cable-glands/';                      // Если id нет, то создаем новую запись

    const method = this.formData.id ? 'PUT' : 'POST';   // Если id есть, то обновляем, иначе создаем

    const response = await fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(this.formData),
    });

    if (response.ok) {
      alert('Данные успешно сохранены!');
    } else {
      alert('Ошибка при сохранении данных!');
    }
  } catch (error) {
    console.error(error);
    alert('Ошибка при подключении к серверу');
  }
}

  }
};
</script>

