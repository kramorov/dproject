<template>
  <div>
    <!-- Блок 1: Список запросов клиентов -->
    <div>
<!--      <AppActionButton type="Добавить запрос" @click="addItem(item.id)" />-->
      <button
        :disabled="!selectedItem"
        @click="openEditForm"
        class="w3-button w3-teal w3-margin-right">
        Изменить запрос
      </button>
      <ul class="w3-ul">
        <li
          v-for="request in request_list_items"
          :key="request.id"
          class="w3-bar"
          :class="{ 'w3-light-gray': selectedItem?.id === request.id }"
          @click="selectItem(request)"
          @dblclick="openEditForm(request)"
        >
          <div class="w3-card-2 w3-padding">
            <!-- Таблица для отображения данных -->
            <table class="w3-table w3-bordered w3-small">
              <tbody>
                <!-- Первая строка -->
                <tr>
                  <td>{{ request.request_type }}</td>
                  <td>{{ request.symbolic_code }}</td>
                  <td>Дата: {{ request.formatted_request_date_str }}</td>
                </tr>
                <!-- Вторая строка -->
                <tr>
                  <td>{{ request.request_from_client_company }}</td>
                  <td>{{ request.request_responsible_person }}</td>
                  <td colspan="3">Обновлено: {{ request.formatted_updated_at_str }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </li>
      </ul>
    </div>

    <!-- Блок 2: Список строк для выбранного запроса -->
    <div v-if="selectedItem" class="w3-margin-top">
      <h3>Строки для запроса: {{ selectedItem.symbolic_code }}</h3>
      <ul class="w3-ul">
        <li
          v-for="line in request_lines"
          :key="line.id"
          class="w3-bar w3-card-2 w3-padding"
        >
          <div>
            ->{{ line.id }} - № {{ line.item_no }} - Номер строки в запросе: {{ line.request_line_number}} - ОЛ: {{ line.request_line_ol }}
          </div>
        </li>
      </ul>
    </div>

     Форма редактирования
    <ClientRequestEditPage
      v-if="isEditFormVisible"
      :request_ptr="selectedItem"
      @close="closeEditForm"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import axios from "axios";
import { API_URL } from "../../config/api.js";
// import EditRequestItem from "../client_request/EditRequestItem.vue";
import ClientRequestEditPage from "../client_request/ClientRequestEditPage.vue";
import AppActionButton from "../../components/AppActionButton.vue"

export default {
  name: 'ClientRequest',
  components: {ClientRequestEditPage, AppActionButton },
  setup() {
    // Реактивные переменные
    const request_list_items = ref([]);
    const request_lines = ref([]); // Строки для выбранного запроса
    const pagination = ref({ next: null, previous: null }); // Пагинация
    const currentRequest = ref({
      id: null,
      symbolic_code: '',
      request_type: '',
      request_from_client_company: '',
      request_responsible_person: '',
      formatted_request_date_str: '',
      formatted_created_at_str: '',
      formatted_updated_at_str: ''
    });
    const isFormVisible = ref(false);
    const isEditing = ref(false);
    const selectedItem = ref(null); // Выбранный элемент
    const isEditFormVisible = ref(false); // Видимость формы редактирования

    // Вычисляемое свойство
    const formTitle = computed(() => {
      return isEditing.value ? 'Редактировать запрос' : 'Добавить запрос';
    });

    // Методы
        // Метод для выбора элемента
    const selectItem = (request) => {
      if (selectedItem.value?.id === request.id) {
        // Если элемент уже выбран, снимаем выбор
        console.log('SET selectedItem.value to NULL',selectedItem.value)
        selectedItem.value = null;
        console.log('NOW selectedItem.value',selectedItem.value)
      } else {
        // Иначе выбираем элемент
        selectedItem.value = request;
        console.log('NEW selectedItem.value',selectedItem.value)
        fetchRequestLines();
      }
    };


    // Метод для открытия формы редактирования
    const openEditForm = (request) => {
      // selectedItem.value = request.id;
      isEditFormVisible.value = true;
      console.log("openEditForm", selectedItem.value.id)
      // console.log(request_list_items)
    };

    // Метод для закрытия формы редактирования
    const closeEditForm = () => {
      isEditFormVisible.value = false;
      selectedItem.value = null; // Сброс выбранного элемента
    };
    const showCreateForm = () => {
      isEditing.value = false;
      currentRequest.value = {
        id: null,
        symbolic_code: '',
        request_type: null,
        request_date: ''
      };
      isFormVisible.value = true;
    };

    const editRequest = (request) => {
      isEditing.value = true;
      currentRequest.value = { ...request };
      isFormVisible.value = true;
    };

    const hideForm = () => {
      isFormVisible.value = false;
    };

    const saveRequest = () => {
      // Здесь должен быть вызов API для сохранения или обновления запроса
      if (isEditing.value) {
        // Обновить запрос
      } else {
        // Создать новый запрос
      }
      hideForm();
      fetchRequestList();
    };

    const deleteRequest = (id) => {
      // Здесь должен быть вызов API для удаления запроса
      fetchRequestList();
    };

    const fetchRequestList = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/client_requests/clientrequestlist/`);
        request_list_items.value = response.data.results;
        // console.log('Ответ сервера:', response);
        // console.log('Данные:', response.data.results);
      } catch (error) {
        console.error('Ошибка при получении данных:', error);
      }
    };
        // Загрузка строк для выбранного запроса
    const fetchRequestLines = async (url = `${API_URL}/api/client_requests/client-request-lines-list/`) => {
      if (!selectedItem.value) return;

      try {
        const response = await axios.get(url, {
          // params: {selectedItem.value.id }, // Фильтр по выбранному запросу
          params: { request_id: selectedItem.value.id }, // Фильтр по выбранному запросу
        });
        request_lines.value = response.data;
        // console.log(response.data)
        // console.log(response.data.results)
        // console.log(request_lines)
        pagination.value = {
          next: response.data.next,
          previous: response.data.previous,
        };
      } catch (error) {
        console.error('Ошибка при загрузке строк запроса:', error);
      }
    };

    const fetchRequestTypes = () => {
      // Здесь должен быть вызов API для получения списка типов запросов
    };

    // Хук жизненного цикла
    onMounted(() => {
      fetchRequestList();
      fetchRequestTypes();
    });

    // Возвращаем все переменные и методы, чтобы они были доступны в шаблоне
    return {
      request_list_items,
      currentRequest,
      isFormVisible,
      isEditing,
      selectedItem,
      isEditFormVisible,
      formTitle,
      selectItem,
      request_lines,
      pagination,
      openEditForm,
      closeEditForm,
      showCreateForm,
      editRequest,
      hideForm,
      saveRequest,
      deleteRequest,
      fetchRequestList,
      fetchRequestLines,
      fetchRequestTypes
    };
  }
};
</script>