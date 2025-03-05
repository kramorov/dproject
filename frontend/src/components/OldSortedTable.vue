<template>
  <div>
<!--    <h1 class="w3-text-primary">Список вариантов приводов</h1>-->
    <h1 class="w3-text-primary">{{ showActuatorEditPage ? 'Список вариантов приводов (Редактирование)' : 'Список вариантов приводов (False)' }}</h1> <!-- Динамическое изменение заголовка -->
    <div class="actions w3-margin-bottom">
      <button
        :disabled="!selectedRows.length"
        @click="deleteRecords"
        class="w3-button w3-red w3-margin-right">
        Удалить записи
      </button>

      <button
        :disabled="!selectedRows.length"
        @click="editRecords"
        class="w3-button w3-teal w3-margin-right">
        Редактировать
      </button>

      <button
        @click="createNewRecord"
        class="w3-button w3-teal w3-margin-right">
        Создать
      </button>
      <ActuatorEdit v-if="showActuatorEditPage" />
      <button
        :disabled="!selectedRows.length"
        @click="copyRecords"
        class="w3-button w3-teal">
        Добавить копированием
      </button>
    </div>

    <div class="list-container w3-padding-large">
      <!-- Передаем данные и структуру колонок в UnsortedTable -->
      <UnsortedTable
        :actuators="actuators"
        :columns="columns"
        :selectedRows="selectedRows"
        @toggleSelection="toggleSelection"
      />
    </div>

    <div v-if="showDeleteConfirm" class="w3-modal" style="display:block;">
      <div class="w3-modal-content w3-card-4 w3-animate-zoom">
        <div class="w3-container w3-padding">
          <p>Вы действительно хотите удалить выделенные записи?</p>
          <button @click="confirmDelete" class="w3-button w3-green w3-margin-right">Да</button>
          <button @click="cancelDelete" class="w3-button w3-red">Нет</button>
        </div>
      </div>
    </div>
  </div>
</template>


<script>
import { ref, onMounted } from 'vue';
import { fetchActuators, deleteActuators, copyActuators } from '../services/api.js';
import UnsortedTable from './UnsortedTable.vue';
import ActuatorEdit from './ActuatorEdit1.vue';

export default {
  name: 'ActuatorList',
  components: { UnsortedTable, ActuatorEdit },
  setup: function () {
    const actuators = ref([]);
    const selectedRows = ref([]);
    const showDeleteConfirm = ref(false); // Это ref, работаем через .value
    const showActuatorEditPage = ref(false); // Флаг для отображения компонента
    // Структура колонок таблицы
    const columns = ref([
      {title: 'Статус', field: 'status', key: 'status'},
      {title: 'Название привода', field: 'name', key: 'name'},
      {title: 'Модель привода', field: 'actual_model_name', key: 'actual_model' },
      {title: 'Создан', field : 'date_created', key :   'date_created'},
      {title: 'Последнее редактирование', field:'date_updated', key:'date_updated'},
    // Можете добавить любые другие колонки, указав соответствующие ключи полей
  ]);


    onMounted(async () => {
      actuators.value = await fetchActuators();
      console.log(actuators.value)
    });

    const toggleSelection = (id) => {
      if (selectedRows.value.includes(id)) {
        selectedRows.value = selectedRows.value.filter(item => item !== id);
      } else {
        selectedRows.value.push(id);
      }
    };

    const deleteRecords = () => {
      showDeleteConfirm.value = true; // Устанавливаем через .value
    };

    const confirmDelete = async () => {
      await deleteActuators(selectedRows.value);
      actuators.value = actuators.value.filter(actuator => !selectedRows.value.includes(actuator.id));
      selectedRows.value = [];
      showDeleteConfirm.value = false; // Устанавливаем через .value
    };

    const cancelDelete = () => {
      showDeleteConfirm.value = false; // Устанавливаем через .value
    };

    const copyRecords = async () => {
      await copyActuators(selectedRows.value);
      actuators.value = await fetchActuators();
    };

    const editRecords = () => {
      // Логика для редактирования записей
    };

    const createNewRecord = () => {
      // Логика для создания нового записи
      showActuatorEditPage.value = !showActuatorEditPage.value; // Переключаем флаг для отображения компонента
      console.log('Create')
    };

    return {
      actuators,
      selectedRows,
      showDeleteConfirm,
      columns,  // Передаем структуру колонок
      toggleSelection,
      deleteRecords,
      confirmDelete,
      cancelDelete,
      copyRecords,
      editRecords,
      createNewRecord,
      showActuatorEditPage,
    };
  }
};
</script>

<style scoped>
.actuator-row.selected {
  background-color: #e0f7fa;
}

.list-container {
  max-height: 400px;
  overflow-y: auto;
}

button:disabled {
  background-color: #ddd;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 10px;
  border: 1px solid #ddd;
  text-align: left;
}

th {
  cursor: pointer;
  background-color: #f4f4f4;
}

.selected {
  background-color: #e0f7fa;
}
</style>
