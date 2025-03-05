<template>
  <div class="actuator-edit">
    <div class="form">
      <div>
        <label for="actual_model_line">Модель</label>
        <select v-model="formData.actual_model_line" @change="fetchModels">
          <option v-for="line in modelLines" :value="line.id" :key="line.id">{{ line.name }}</option>
        </select>
      </div>

      <div>
        <label for="actual_voltage">Напряжение</label>
        <select v-model="formData.actual_voltage">
          <option v-for="voltage in voltages" :value="voltage.id" :key="voltage.id">{{ voltage.name }}</option>
        </select>
      </div>

      <div>
        <label for="actual_model">Модель</label>
        <select v-model="formData.actual_model">
          <option v-for="model in models" :value="model.id" :key="model.id">{{ model.name }}</option>
        </select>
      </div>

      <button @click="fillDefaults">Заполнить по коду</button>

      <div v-if="error">
        <p>{{ errorText }}</p>
      </div>

      <!-- Form fields for other attributes go here -->

      <button @click="saveRecord">Сохранить</button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { fetchModelLines, fetchVoltages, fetchModels, fetchModelData, processStringWithModelName } from '../api/api.js';

export default {
  name: 'ActuatorEdit',
  props: {
    actuatorId: {
      type: Number,
      required: true
    }
  },
  setup(props) {
    const formData = ref({});
    const modelLines = ref([]);
    const voltages = ref([]);
    const models = ref([]);
    const error = ref(false);
    const errorText = ref('');

    onMounted(async () => {
      modelLines.value = await fetchModelLines();
      voltages.value = await fetchVoltages();
    });

    const fetchModels = async () => {
      models.value = await fetchModels(formData.value.actual_model_line, formData.value.actual_voltage);
    };

    const fillDefaults = async () => {
      try {
        const response = await processStringWithModelName(formData.value);
        if (response.error) {
          error.value = true;
          errorText.value = response.errorText;
        } else {
          error.value = false;
          formData.value = { ...formData.value, ...response.data };
        }
      } catch (err) {
        error.value = true;
        errorText.value = 'Ошибка при заполнении данных';
      }
    };

    const saveRecord = async () => {
      try {
        // Logic to save record here (create or update)
        console.log('Saving record', formData.value);
      } catch (err) {
        console.log('Error saving record', err);
      }
    };

    return {
      formData,
      modelLines,
      voltages,
      models,
      error,
      errorText,
      fetchModels,
      fillDefaults,
      saveRecord
    };
  }
};
</script>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
}

button:disabled {
  background-color: #ddd;
}
</style>
