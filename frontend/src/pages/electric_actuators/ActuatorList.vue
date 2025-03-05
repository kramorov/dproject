<template>
  <h1>{{ showActuatorEdit ? 'Список вариантов приводов (Редактирование)' : 'Список вариантов приводов (False)' }}</h1> <!-- Динамическое изменение заголовка -->
    <div class="actuator-list">
    <div class="actions">
      <button :disabled="!selectedRows.length" @click="deleteRecords">Удалить записи</button>
      <button :disabled="!selectedRows.length" @click="editRecords">Редактировать</button>
      <button @click="createNewRecord">Создать</button>
        <!-- Условное отображение компонента ActuatorList -->
<!--        <ActuatorEdit v-if="showActuatorEdit" />-->
      <button :disabled="!selectedRows.length" @click="copyRecords">Добавить копированием</button>
    </div>

  <div class="list-container">
     <div>
      <SortableTable
        :data="actuators"
        :columns="columns"
        :selectedRows="selectedRows"
        @update:selectedRows="updateSelectedRows" />
      </div>
    </div>

    <div v-if="showDeleteConfirm">
      <p>Вы действительно хотите удалить выделенные записи?</p>
      <button @click="confirmDelete">Да</button>
      <button @click="cancelDelete">Нет</button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { fetchActuators, deleteActuators, copyActuators } from '../../services/api.js';
import SortableTable from '../../components/SortableTable.vue';
import ActuatorEdit from '../../components/ActuatorEdit1.vue';

export default {
  name: 'ActuatorList',
  components: {SortableTable, ActuatorEdit},
  // methods: {
  //   createNewRecord() {
  //     console.log('Create')
  //     this.showActuatorList = !this.showActuatorList; // переключаем состояние
  //   }
  // },
  setup() {
    const actuators = ref([]);
    const selectedRows = ref([]);  // Хранение выбранных строк
    const showDeleteConfirm = ref(false);
    const columns = ref([
      { key: 'id', label: 'ID' },
      { key: 'name', label: 'Наименование' },
      { key: 'type', label: 'Тип' },
      { key: 'status', label: 'Статус' },
      // Можно добавить другие колонки в зависимости от данных
    ]);
    const showActuatorEdit = ref(false); // Флаг для отображения компонента

    onMounted(async () => {
      actuators.value = await fetchActuators();
      console.log(actuators.value);
    });

    // Метод для обработки изменения выделенных строк в таблице
    const updateSelectedRows = (newSelectedRows) => {
      selectedRows.value = newSelectedRows;
    };

    const deleteRecords = () => {
      showDeleteConfirm.value = true;
    };

    const confirmDelete = async () => {
      await deleteActuators(selectedRows.value);
      // Обновляем список актюаторов, удаляя те, которые были выбраны
      actuators.value = actuators.value.filter(actuator => !selectedRows.value.includes(actuator.id));
      selectedRows.value = [];  // Сбрасываем выбранные строки
      showDeleteConfirm.value = false;  // Закрываем окно подтверждения удаления
    };

    const cancelDelete = () => {
      showDeleteConfirm.value = false;  // Закрываем окно подтверждения без изменений
    };

    const copyRecords = async () => {
      await copyActuators(selectedRows.value);
      // Обновляем список после копирования
      actuators.value = await fetchActuators();
    };

    const editRecords = () => {
      // Логика для редактирования записей
      // Можно, например, перенаправить на страницу редактирования или открыть форму
    };

    const createNewRecord = () => {
      // Логика для создания нового записи
      console.log('Create')
      showActuatorEdit.value = !showActuatorEdit.value; // Переключаем флаг для отображения компонента
    };

    return {
      actuators,
      selectedRows,
      showDeleteConfirm,
      updateSelectedRows,  // Убедитесь, что эта функция возвращена
      deleteRecords,
      confirmDelete,
      cancelDelete,
      copyRecords,
      editRecords,
      createNewRecord
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
