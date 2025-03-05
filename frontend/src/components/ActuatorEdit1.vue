<template>
  <div class="actuator-edit">
    <!-- Модальное окно -->
    <div id="modal" class="w3-modal" :class="{ 'w3-show': isModalOpen }">
      <div class="w3-modal-content w3-animate-zoom">
        <header class="w3-container w3-blue">
          <span @click="closeModal" class="w3-button w3-display-topright">&times;</span>
          <h2>Редактирование активации</h2>
        </header>

        <div class="w3-container">
          <table style="width: 100%; border-collapse: collapse;">
            <tr>
              <td style="padding-right: 10px;">
                <label for="actual_model_line">Серия приводов</label>
              </td>
              <td>
                <select v-model="formData.actual_model_line" class="w3-select w3-border">
                  <option v-for="line in modelLines" :value="line.id" :key="line.id">{{ line.name }}</option>
                </select>
              </td>
              <td style="padding-left: 10px;">
                <label for="actual_voltage">Напряжение</label>
              </td>
              <td>
                <select v-model="formData.actual_voltage" class="w3-select w3-border">
                  <option v-for="voltage in voltages" :value="voltage.id" :key="voltage.id">{{ voltage.symbolic_code }}</option>
                </select>
              </td>
<!--              <td v-show="formData.actual_model_line && formData.actual_voltage" style="padding-left: 10px;">-->
                 <td v-if="formData.actual_model_line && formData.actual_voltage" style="padding-left: 10px;">
                    <label for="actual_model">Модель</label>
                  </td>
                  <td v-if="formData.actual_model_line && formData.actual_voltage">
                    <select v-model="formData.actual_model" class="w3-select w3-border" :disabled="!formData.actual_model_line || !formData.actual_voltage">
                      <option v-for="model in models" :value="model.id" :key="model.id">{{ model.name }}</option>
                    </select>
                  </td>
                  <td v-else style="padding-left: 10px;">
                    <label for="actual_model">Модель</label>
                  </td>
                  <td v-else>
                    <select class="w3-select w3-border" disabled>
                      <option value="">Выберите модель</option>
                    </select>
                  </td>
            </tr>
          </table>
          <button @click="fillDefaults" class="w3-button w3-green w3-block">Заполнить по коду</button>

          <div v-if="error" class="w3-panel w3-red w3-margin-top">
            <p>{{ errorText }}</p>
          </div>

          <!-- Дополнительные поля формы -->

          <button @click="saveRecord" class="w3-button w3-blue w3-block w3-margin-top">Сохранить</button>

          </div>
      </div>
    </div>

    <!-- Кнопка для открытия модального окна -->
<!--    <button @click="openModal" class="w3-button w3-blue">Открыть форму</button>-->
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue';
import {fetchModelLines, fetchVoltages, fetchModels, fetchActuators} from '../services/api.js';


export default {
  name: 'ActuatorEdit',
  setup() {
    // Объявляем реактивные переменные с использованием ref()
    const isModalOpen = ref(true);
    const modelIsSelected = ref(false);
    const formData = ref({
      actual_model_line: null,
      actual_voltage: null,
      actual_model: null
    });
    const modelLines = ref([]);
    const voltages = ref([]);
    const models = ref([]);
    const error = ref(false);
    const errorText = ref('');


    // Запрос при монтировании компонента
    onMounted(async () => {
      try {
        modelLines.value = await fetchModelLines();  // Вызываем функцию при монтировании
        voltages.value = await fetchVoltages();
        // console.log(modelLines.value)
        // console.log(voltages.value)
      } catch (err) {
        console.error('Ошибка в setup:', err);
      }
    });
        // Функция для загрузки моделей в зависимости от значений actual_model_line и actual_voltage
    const fetchModelsData = async () => {
      if (formData.value.actual_model_line !== null && formData.value.actual_voltage !== null) {
        try {
          // console.log('actual_model_line')
          console.log(formData.value.actual_model_line)
          // console.log('actual_voltage')
          // console.log(formData.value.actual_voltage)
          models.value = await fetchModels(formData.value.actual_model_line, formData.value.actual_voltage);
          console.log('models')
          console.log(models.value)
          modelIsSelected.value = true;
        } catch (err) {
          console.error('Ошибка при получении моделей:', err);
        }
      }
    };

    // Следим за изменениями значений actual_model_line и actual_voltage
    watch([() => formData.value.actual_model_line, () => formData.value.actual_voltage], () => {
      // Сбрасываем модель при изменении параметров
      formData.value.actual_model = null;
      fetchModelsData();  // Вызываем fetchModelsData, когда оба значения изменяются
    });

    // Методы для модального окна
    const openModal = () => {
      isModalOpen.value = true;
    };

    const closeModal = () => {
      isModalOpen.value = false;
    };

    return {
      isModalOpen,
      formData,
      modelLines,
      voltages,
      models,
      error,
      errorText,
      openModal,
      closeModal
    };
  }
};
</script>

<style scoped>
/* Если необходимо, можно стилизовать модальное окно */
.w3-modal {
  display: none;
  z-index: 9999;
}

.w3-show {
  display: block;
}
</style>
