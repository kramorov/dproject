<template>
  <div class="w3-container w3-light-grey w3-padding" >
    <!-- Блок 1: Список запросов клиентов -->
    <div>
      <button @click="openRequestForm()"
        class="w3-button w3-teal w3-margin-bottom">
        <i class="fa fa-plus"></i> Создать новый запрос
      </button>
      <ul class="w3-ul">
        <li
          v-for="request in request_list_items"
          :key="request.id"
          class="w3-bar"
          :class="{ 'w3-light-gray': selectedItem?.id === request.id }"
          @click="selectItem(request)"
          @dblclick="openRequestForm(request)"
        >
          <div class="w3-card-2 w3-padding">
            <!-- Таблица для отображения данных -->
            <table class="w3-table w3-bordered w3-small">
              <tbody>
                <!-- Первая строка -->
                <tr>
                  <td>{{ request.request_status.text_description }}</td>
                  <td>{{ request.request_type.symbolic_code }}</td>
                  <td>{{ request.symbolic_code }}</td>
                  <td>Дата: {{ request.request_date }}</td>
                  <td>
                    <EditButtonComponent
                      :item="request"
                      label = "Редактировать"
                      @edit="openRequestForm"
                    />
<!--                    <button @click="openRequestForm(request)" class="w3-button w3-small w3-teal">-->
<!--                      <i class="fa fa-edit"></i> Редактировать-->
<!--                    </button>-->
                  </td>
                </tr>
                <!-- Вторая строка -->
                <tr>
                  <td>{{ request.request_from_client_company.symbolic_code }}</td>
                  <td>{{ request.request_responsible_person.symbolic_code }}</td>
                  <td colspan="3">Обновлено: {{ request.updated_at ? new Date(request.updated_at).toISOString().split('T')[0] : '' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </li>
      </ul>
    </div>

    <!-- Блок 2: Список строк для выбранного запроса -->
    <div v-if="selectedItem" class="w3-margin-top w3-bordered">
      <div v-if="selectedItem_data_is_ready === true">
        <div class="w3-card-2 w3-padding">
          <table class="w3-table w3-bordered w3-small">
            <thead>
              <tr class="w3-center">
                <th>№ позиции</th>
                <th>№ строки запроса</th>
                <th>ОЛ</th>
                <th>Арматура</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="line in request_lines" :key="line.id">
                <td>{{ line.item_no }}</td>
                <td>{{ line.request_line_number }}</td>
                <td>{{ line.request_line_ol }}</td>
                <td>{{ line.valve_requirement.valve_requirement_text_description }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>git pull
    </div>
      Модальное окно с формой создания/редактирования запроса
    <client-request-form
      v-model:showForm="showRequestForm"
      :initial-data="currentRequest"
      :is-edit-mode="isEditMode"
      @submit="handleFormSubmit"
      @cancel="closeRequestForm"
    />
  </div>
</template>

<script>
import {ref, computed, onMounted, nextTick} from 'vue';
import axios from "axios";
import { API_URL } from "@/config/api.js";
import AppActionButton from "../../components/AppActionButton.vue"
import ClientRequestForm from './ClientRequestForm.vue'
import EditButtonComponent from "@/pages/client_request/components/EditButtonComponent.vue";

export default {
  name: 'ClientRequest',
  components: {EditButtonComponent, AppActionButton, ClientRequestForm },
  setup() {
    // Реактивные переменные
    const request_list_items = ref([]);
    const request_lines = ref([]); // Строки для выбранного запроса
    const pagination = ref({ next: null, previous: null }); // Пагинация



    const currentRequest = ref(false);
    const isEditing = ref(false);
    const isEditMode = ref(false);
    const showRequestForm = ref(false)
    const selectedItem = ref(null); // Выбранный элемент
    const selectedItem_data_is_ready = ref(false);
    const isEditFormVisible = ref(false); // Видимость формы редактирования

    // Вычисляемое свойство
    const formTitle = computed(() => {
      return isEditing.value ? 'Редактировать запрос' : 'Добавить запрос';
    });

    // Методы
    const openRequestForm = (request = null) => {
      // console.log('openRequestForm request =',request)
      // console.log('openRequestForm start showRequestForm.value',showRequestForm.value)
      if (request!==null) {
        // Режим редактирования
        currentRequest.value = JSON.parse(JSON.stringify(request))
        // console.log('Режим редактирования currentRequest.value',currentRequest.value)
        isEditMode.value = true
      } else {
        // Режим создания
        currentRequest.value = {
          id: null,
          symbolic_code: '',
          request_type: '',
          request_from_client_company: '',
          request_responsible_person: '',
          end_customer: '',
          request_date: '',
          created_at: '',
          updated_at: ''
        }
        console.log('Режим создания currentRequest.value',currentRequest.value)
        isEditMode.value = false
      }
      showRequestForm.value = true
      // console.log('openRequestForm finished showRequestForm.value',showRequestForm.value)
    }
    const closeRequestForm = () => {
      // console.log('closeRequestForm start showRequestForm.value',showRequestForm.value)
      showRequestForm.value = false
      currentRequest.value = null
      // console.log('closeRequestForm finished showRequestForm.value',showRequestForm.value)
    }
    // Создание и редактирование запроса
    // const fetchRequestList = async () => {
    const createRequest = async (formData) => {
      try {
        const response = await axios.post('/api/client_requests/clientrequestlist/',formData);
      } catch (error) {
        console.error('Ошибка при создании запроса:', error);
        // Обработка ошибок валидации
        if (error.response && error.response.data) {
          alert(`Ошибка: ${JSON.stringify(error.response.data)}`);
        } else {
          alert('Произошла ошибка при создании запроса');
        }
      }
    };
    const updateRequest = async (formData)=>  {
      if (!currentRequest.value?.id) return;
      try {
        const response = await axios.patch(
          `/api/client_requests/clientrequestlist/${currentRequest.value.id}/`,formData);
      } catch (error) {
        console.error('Ошибка при обновлении запроса:', error);
        // Обработка ошибок валидации
        if (error.response && error.response.data) {
          alert(`Ошибка: ${JSON.stringify(error.response.data)}`);
        } else {
          alert('Произошла ошибка при обновлении запроса');
        }
      }
    };
    const handleFormSubmit = async (formData) => {
      console.error('handleFormSubmit start')
      try {
        if (isEditMode.value) {
          await updateRequest(formData)
        } else {
          await createRequest(formData)
        }
        closeRequestForm()
        await fetchRequestList()
      } catch (error) {
        console.error('Ошибка:', error)
        alert('Произошла ошибка при сохранении')
      }
    }

    // Метод для выбора элемента
    const selectItem = (request) => {
      if (selectedItem.value?.id === request.id) {
        // Если элемент уже выбран, снимаем выбор
        selectedItem.value = null;
        selectedItem_data_is_ready.value=false;
      } else {
        // Иначе выбираем элемент
        console.log('Selected request id=', request.id)
        selectedItem.value = request;
        selectedItem_data_is_ready.value=false;
        // Загружаем строки только если selectedItem.value корректен
        if (selectedItem.value?.id) {
          fetchRequestLines();
        } else {
          console.error('Выбранный элемент не имеет id!');
        }
        // console.log('125:NOW selectedItem_data_is_ready.value',selectedItem_data_is_ready.value)
      }
    };
    const fetchRequestList = async () => {
      try {
        const response = await axios.get(`${API_URL}/api/client_requests/clientrequestlist/`);
        request_list_items.value = response.data.results;
        // console.log('Ответ сервера:', response);
        // console.log('Данные:', response.data.results);
      } catch (error) {
        console.error('193:Ошибка при получении данных:', error);
      }
    };
    // Загрузка строк для выбранного запроса  client-request-items/?parent_id=2
    const fetchRequestLines = async (url = `${API_URL}/api/client_requests/client-request-items/`) => {
      if (!selectedItem.value?.id) { // Проверяем и selectedItem.value, и его id
        console.error('selectedItem.value.id не существует!');
        selectedItem_data_is_ready.value = false;
        return;
      }

      try {
        const response = await axios.get(url, {
          // params: {selectedItem.value.id }, // Фильтр по выбранному запросу
          params: { parent_id: selectedItem.value.id}, // Фильтр по выбранному запросу
        });
        // await nextTick()
        request_lines.value = response.data.results;
        // console.log(request_lines.value)
        // console.log(response.data.results)
        // console.log(request_lines)
        // pagination.value = {
        //   next: response.data.next,
        //   previous: response.data.previous,
        // };
        // await nextTick()
        // console.log('Before setting:', selectedItem_data_is_ready)
        selectedItem_data_is_ready.value = true
        // console.log('After setting:', selectedItem_data_is_ready)
      } catch (error) {
        // await nextTick()
        // console.error('Ошибка при загрузке строк запроса:', error);
        selectedItem_data_is_ready.value=false;
      }
    };

    // Хук жизненного цикла
    onMounted(() => {
      fetchRequestList();
    });

    // Возвращаем все переменные и методы, чтобы они были доступны в шаблоне
    return {
      request_list_items,
      showRequestForm,
      currentRequest,
      isEditMode,
      openRequestForm,
      closeRequestForm,
      handleFormSubmit,
      createRequest, updateRequest,
      selectedItem,
      formTitle,
      selectItem,
      selectedItem_data_is_ready,
      request_lines,
      pagination,
      fetchRequestList,
      fetchRequestLines
    };
  }
};
</script>

<style scoped>
/* Добавьте это временно для тестирования */
.modal-class {  /* или какой класс использует ваше модальное окно */
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
  z-index: 1000;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>