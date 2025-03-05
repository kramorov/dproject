<template>
  <div>
    <h1>Материалы для кабельных вводов</h1>
<!--    <form @submit.prevent="createCableGlandBodyMaterial">-->
<!--      <input v-model="newMaterial.name" placeholder="Название" />-->
<!--      <input v-model="newMaterial.text_description" placeholder="Описание" />-->
<!--      <button type="submit">Создать</button>-->
<!--    </form>-->
    <!-- Кнопка для создания нового материала -->
    <button class="add-button" @click="openCreateModal">➕ Создать материал</button>
     <ul class='cg_body_materials_list'>
      <!-- Заголовки таблицы -->
      <li class="header">
        <div>Название</div>
        <div>Описание</div>
        <div>Удалить</div>
        <div>Изменить</div>
      </li>

      <!-- Данные -->
      <li v-for="material in materials" :key="material.id">
        <div>{{ material.name }}</div>
        <div>{{ material.text_description }}</div>
        <button @click="deleteMaterial(material.id)">🗑</button>
<!--        <AppActionButton type="Открыть" @click="openEditModal(material.id)" />-->
<!--        <AppActionButton type="Удалить" @click="deleteMaterial(material.id)" />-->
         <button @click="openEditModal(material)">✏️</button>

      </li>
    </ul>
        <!-- Используем модальное окно -->
    <EditModal
      v-if="isModalOpen"
      :material="editingMaterial"
      @save="handleSaveMaterial"
      @close="closeModal"
    />
     <ErrorModal
      :message="errorMessage"
      :visible="showErrorModal"
      @close="closeErrorModal"
    />
<!--    <div v-if="editingMaterial">-->
<!--      <h3>Редактировать</h3>-->
<!--      <input v-model="editingMaterial.name" placeholder="Название" />-->
<!--      <input v-model="editingMaterial.text_description" placeholder="Описание" />-->
<!--      <button @click="saveEditedMaterial">Сохранить</button>-->
<!--      <button @click="cancelEdit">Отменить</button>-->
<!--    </div>-->
  </div>
</template>

<script>
import axios from 'axios';
import { API_URL } from "../../config/api.js";
import EditListItem from "../../components/EditListItem.vue";
import EditModal from "../../components/EditModal.vue";
import { handleApiError } from "../../services/apiErrorHandler"; // Импортируем обработчик ошибок
import ErrorModal from "../../components/ErrorModal.vue"; // Импортируем компонент модального окна
import AppActionButton from "../../components/AppActionButton.vue";


export default {
  components: {
    EditListItem,
    EditModal,
    ErrorModal,  // Добавляем модальное окно как компонент
    AppActionButton,
  },
  data() {
    return {
      materials: [],
      newMaterial: { name: '', text_description: '' },
      editingMaterial: null, // Если null, то создаётся новый материал
      isModalOpen: false, // Открыто ли модальное окно
      errorMessage: null,  // Добавляем состояние для хранения ошибки
      showErrorModal: false,  // Флаг для отображения модального окна
    };
  },
  created() {
    this.fetchMaterials();
  },
  methods: {
    fetchMaterials() {
      axios.get(`${API_URL}/cg/cable-glands-materials/`)
        .then(response => {
          this.materials = response.data;
          this.errorMessage = null; // Сброс ошибки, если запрос успешен
        })
      .catch(error => {
          console.log("Ошибка перехвачена:", error);
          this.errorMessage = handleApiError(error);  // Используем обработчик и сохраняем текст ошибки в состоянии
          this.showErrorModal = true;  // Показываем модальное окно с ошибкой
        });
    },
    createCableGlandBodyMaterial() {
      axios.post(`${API_URL}/cg/cable-glands-materials/`, this.newMaterial)
        .then(response => {
          this.materials.push(response.data);
          this.newMaterial = { name: '', text_description: '' };
          this.errorMessage = null; // Сброс ошибки
        })
        .catch(error => {
            this.errorMessage = handleApiError(error);  // Используем обработчик и сохраняем текст ошибки в состоянии
            this.showErrorModal = true;  // Показываем модальное окно с ошибкой
          });
    },
    deleteMaterial(id) {
      axios.delete(`${API_URL}/cg/cable-glands-materials/${id}/`)
        .then(() => {
          this.materials = this.materials.filter(material => material.id !== id);
        })
        .catch(error => {
            this.errorMessage = handleApiError(error);  // Используем обработчик и сохраняем текст ошибки в состоянии
            this.showErrorModal = true;  // Показываем модальное окно с ошибкой
          });
    },
    openEditModal(material) {
      this.editingMaterial = { ...material }; // Копируем материал для редактирования
      this.isModalOpen = true;
    },
    openCreateModal() {
      this.editingMaterial = null; // Открываем пустое модальное окно для создания
      this.isModalOpen = true;
    },
    handleSaveMaterial(material) {
      if (material.id) {
        // Если у объекта есть ID, значит это редактирование
        axios.put(`${API_URL}/cg/cable-glands-materials/${material.id}/`, material).then((response) => {
          const index = this.materials.findIndex((m) => m.id === material.id);
          this.materials[index] = response.data;
          this.closeModal();
        })
        .catch(error => {
          this.errorMessage = handleApiError(error);  // Используем обработчик и сохраняем текст ошибки в состоянии
        });
      } else {
        // Если ID нет, значит это создание нового материала
        axios.post(`${API_URL}/cg/cable-glands-materials/`, material).then((response) => {
          this.materials.push(response.data);
          this.closeModal();
        })
        .catch(error => {
          this.errorMessage = handleApiError(error);  // Используем обработчик и сохраняем текст ошибки в состоянии
          this.showErrorModal = true;  // Показываем модальное окно с ошибкой
        });
      }
    },
    closeModal() {
      this.isModalOpen = false;
      this.editingMaterial = null;
    },
    closeErrorModal() {
      this.showErrorModal = false;  // Закрытие модального окна
    },
  },
};
</script>

<style scoped>
/*.material-row {*/
/*  display: flex;*/
/*  align-items: center;*/
/*  justify-content: space-between;*/
/*  background-color: #333;*/
/*  color: #fff;*/
/*  padding: 10px 20px;*/
/*}*/
.material-row {
  display: grid;
  grid-template-columns: 2fr 4fr 1fr 1fr; /* Один столбец */
  gap: 10px; /* Отступы между элементами */
  background-color: #333;
  color: #fff;
  padding: 10px 20px;
}
.cg_body_materials_list {
  width: 100%;
  max-width: 800px; /* Ограничиваем ширину */
  margin: 20px auto;
  border-collapse: collapse;
  list-style: none;
  padding: 0;
}

/* Заголовки (фиксируем ширину столбцов) */
.cg_body_materials_list li {
  display: grid;
  grid-template-columns: 2fr 4fr 1fr 1fr; /* 4 равных столбца */
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid #ddd;
  background-color: #fff;
  transition: background 0.2s ease-in-out;
}

.cg_body_materials_list li:nth-child(odd) {
  background-color: #f8f8f8; /* Полосатый эффект */
}

.cg_body_materials_list li:hover {
  background-color: #e3f2fd; /* Подсветка строки */
}

.cg_body_materials_list li div {
  padding: 8px;
  text-align: left;
}

/* Заголовок таблицы */
.cg_body_materials_list .header {
  font-weight: bold;
  background: #1976d2;
  color: white;
}

/* Кнопки */
.cg_body_materials_list button {
  padding: 6px 10px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  border-radius: 4px;
  transition: 0.3s;
}

.cg_body_materials_list button:first-of-type {
  background: #ff5252;
  color: white;
}

.cg_body_materials_list button:first-of-type:hover {
  background: #d32f2f;
}

.cg_body_materials_list button:last-of-type {
  background: #29b6f6;
  color: white;
}

.cg_body_materials_list button:last-of-type:hover {
  background: #0288d1;
}

</style>
