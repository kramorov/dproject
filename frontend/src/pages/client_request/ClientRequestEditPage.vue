<template>
  <div class="w3-container">
    <!-- Заголовок формы -->
    <div class="w3-card-4 w3-padding">
      <h2>{{ currentRequest.id ? 'Редактирование запроса' : 'Создание запроса' }}</h2>
      <div class="w3-section">
        <label>Symbolic Code:</label>
        <input class="w3-input w3-border" v-model="currentRequest.symbolic_code" type="text" />
      </div>
<!--      <div class="w3-section">-->
<!--        <label>Request Type:</label>-->
<!--        <select class="w3-select w3-border" v-model="currentRequest.request_type">-->
<!--          <option v-for="type in requestTypes" :key="type.id" :value="type.id">-->
<!--            {{ type.name }}-->
<!--          </option>-->
<!--        </select>-->
<!--      </div>-->
<!--       <div class="w3-section">-->
<!--        <label>Client Company:</label>-->
<!--        <select class="w3-select w3-border" v-model="currentRequest.request_from_client_company">-->
<!--          &lt;!&ndash; Добавляем опцию по умолчанию &ndash;&gt;-->
<!--          <option :value="null">Select a company</option>-->
<!--          &lt;!&ndash; Проверяем, что companies существует и не пуст &ndash;&gt;-->
<!--          <template v-if="companies && companies.length > 0">-->
<!--            <option-->
<!--              v-for="company in companies"-->
<!--              :key="company.id"-->
<!--              :value="company.id"-->
<!--            >-->
<!--              {{ company.name }}-->
<!--            </option>-->
<!--          </template>-->
<!--          &lt;!&ndash; Если companies пуст или не определен &ndash;&gt;-->
<!--          <option v-else :value="null" disabled>No companies available</option>-->
<!--        </select>-->
<!--    </div>-->
<!--      <div class="w3-section">-->
<!--        <label>Responsible Person:</label>-->
<!--        <select class="w3-select w3-border" v-model="currentRequest.request_responsible_person">-->
<!--          <option v-for="person in responsiblePersons" :key="person.id" :value="person.id">-->
<!--            {{ person.name }}-->
<!--          </option>-->
<!--        </select>-->
<!--      </div>-->
<!--      <div class="w3-section">-->
<!--        <label>Request Date:</label>-->
<!--        <input class="w3-input w3-border" v-model="currentRequest.request_date" type="date" />-->
<!--      </div>-->
<!--    </div>-->

    <!-- Табличная часть -->
<!--    <div class="w3-card-4 w3-margin-top w3-padding" v-if="currentRequest.id">-->
<!--      <h3>Строки запроса</h3>-->
<!--      <table class="w3-table w3-bordered">-->
<!--        <thead>-->
<!--          <tr>-->
<!--            <th>Item No</th>-->
<!--            <th>Request Line Number</th>-->
<!--            <th>Request Line OL</th>-->
<!--            <th>Actions</th>-->
<!--          </tr>-->
<!--        </thead>-->
<!--        <tbody>-->
<!--          <tr v-for="item in currentRequest.request_lines" :key="item.id">-->
<!--            <td>{{ item.item_no }}</td>-->
<!--            <td>{{ item.request_line_number }}</td>-->
<!--            <td>{{ item.request_line_ol }}</td>-->
<!--            <td>-->
<!--              <button class="w3-button w3-red w3-small" @click="deleteItem(item.id)">Удалить</button>-->
<!--              <button class="w3-button w3-blue w3-small" @click="copyItem(item)">Копировать</button>-->
<!--            </td>-->
<!--          </tr>-->
<!--        </tbody>-->
<!--      </table>-->
<!--      <button class="w3-button w3-green w3-margin-top" @click="addItem">Добавить строку</button>-->
    </div>

    <!-- Кнопки управления -->
    <div class="w3-margin-top">
      <button class="w3-button w3-blue" @click="save">Записать</button>
      <button class="w3-button w3-gray" @click="cancel">Отмена</button>
      <button class="w3-button w3-red" @click="deleteRequest" v-if="currentRequest.id">Удалить</button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useHttp } from '../../composables/useHttp.js'
import axios from "axios";
import {API_URL} from "../../config/api.js";

export default {
  name: 'ClientRequestEditPage',
  props: {
    // request_ptr: {
    //   type: Object,
    //   default: () => ({}),
    // },
    request_ptr: null,
  },
  emits: ['close'],
  setup(props, { emit }) {
    const { get, post, put, del } = useHttp(); // Используем composable для HTTP-запросов
    // Состояние формы
    const currentRequest = ref({
      id: null,
      symbolic_code: '',
      request_type: null,
      request_from_client_company: null,
      request_responsible_person: null,
      formatted_request_date: null,
      request_lines: [],
      formatted_created_at_str: '',
      formatted_updated_at_str: ''
    });

    // Данные для выпадающих списков
    const requestTypes = ref([]);
    const companies = ref([]);
    const responsiblePersons = ref([]);
/**
 * Универсальная функция для выполнения GET-запросов с параметрами.
 * @param {string} url - URL для запроса.
 * @param {object} params - Параметры запроса (query-параметры).
 * @returns {Promise} - Возвращает результат запроса или обрабатывает ошибку.
 */
    const fetchAnyData = async (url, params = {}) => {
      try {
        const response = await axios.get(url, { params });
        return response.data; // Возвращаем данные из ответа
      } catch (error) {
        console.error(`Ошибка при выполнении запроса к ${url}:`, error);

        // Обработка ошибок
        if (error.response) {
          console.error('Статус ошибки:', error.response.status);
          console.error('Данные ошибки:', error.response.data);
        } else if (error.request) {
          console.error('Запрос был выполнен, но ответ не получен');
        } else {
          console.error('Ошибка при настройке запроса:', error.message);
        }

        return null;
      }
    };
    // Загрузка данных для выпадающих списков
    const fetchData = async () => {
      try {
        // requestTypes.value = await get('/api/client_requests/clientrequesttypelist/');
        // companies.value = await get('/api/clients/companies-list/');
        // responsiblePersons.value = await get('/api/clients/company-persons/');
        requestTypes.value = fetchAnyData('/api/client_requests/clientrequesttypelist/');
        companies.value = fetchAnyData('/api/clients/companies-list/');
        responsiblePersons.value = fetchAnyData('/api/clients/company-persons/');
        console.log(requestTypes.value, companies.value, responsiblePersons.value)
      } catch (error) {
        console.error('Ошибка загрузки данных:', error);
      }
    };

    // Сохранение или обновление запроса
    const save = async () => {
      try {
        const url = currentRequest.value.id ? `/api/client-requests/${currentRequest.value.id}/` : '/api/client-requests/';
        const method = currentRequest.value.id ? 'put' : 'post';
        const response = await (method === 'post' ? post(url, currentRequest.value) : put(url, currentRequest.value));
        currentRequest.value = response.data;
      } catch (error) {
        console.error('Ошибка сохранения:', error);
      }
    };

    // Удаление запроса
    const deleteRequest = async () => {
      try {
        await del(`/api/client-requests/${currentRequest.value.id}/`);
        emit('close');
      } catch (error) {
        console.error('Ошибка удаления:', error);
      }
    };

    // Закрытие формы
    const cancel = () => {
      emit('close');
    };

    // Добавление строки
    const addItem = () => {
      // request_lines.value.request_lines.push({
      //   item_no: currentRequest.value.request_lines.length + 1,
      //   request_line_number: '',
      //   request_line_ol: '',
      // });
    };

    // Удаление строки
    const deleteItem = (itemId) => {
      // currentRequest.value.request_lines = currentRequest.value.request_lines.filter(item => item.id !== itemId);
    };

    // Копирование строки
    const copyItem = (item) => {
      // currentRequest.value.request_lines.push({ ...item, id: null });
    };
  const fetchCurrentRequest = async (url = `${API_URL}/api/client_requests/clientrequest/`) => {
    try {
        const response = await axios.get(url, {
          params: {request_id: 1}, // Фильтр по выбранному запросу
          // params: { request_id: selectedItem.value.id }, // Фильтр по выбранному запросу
        });
        // request_lines.value = response.data;
        // console.log(response.data)
        // console.log(response.data.results)
        // console.log(request_lines)
      } catch (error) {
        console.error('Ошибка при загрузке строк запроса:', error);
      }
    };
    // Загрузка данных при монтировании компонента
    onMounted(() => {
      fetchData();
      fetchCurrentRequest();
    });

    return {
      currentRequest,
      requestTypes,
      companies,
      responsiblePersons,
      save,
      cancel,
      deleteRequest,
      addItem,
      deleteItem,
      copyItem,
    };
  },
};
</script>

<style scoped>
.w3-card-4 {
  margin-bottom: 20px;
}
.w3-section {
  margin-bottom: 15px;
}
.w3-button {
  margin-right: 10px;
}
</style>