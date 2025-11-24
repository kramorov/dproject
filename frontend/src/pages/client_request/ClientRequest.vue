<template>
  <div class="w3-container w3-light-grey w3-padding">
    <!-- Блок 1: Список запросов клиентов -->
    <div>
      <button @click="openRequestForm(null)"
              class="w3-button w3-teal w3-margin-bottom">
        <i class="fa fa-plus"></i> Создать новый запрос
      </button>
      <ul class="w3-ul">
        <li
            v-for="request in request_list_items"
            :key="request.id"
            class="w3-bar"
            :class="{ 'w3-light-blue': selectedItem?.id === request.id }"
            @click="selectItem(request)"
            @dblclick="openRequestForm(request)"
        >
          <div class="w3-card-2 w3-padding">
            <!-- Таблица для отображения данных -->
            <table class="w3-table w3-bordered w3-small">
              <tbody >
              <!-- Первая строка -->
              <tr>
                <td>{{request.request_status.text_description}}</td>
                <td>{{request.request_type.symbolic_code}}</td>
                <td>{{request.symbolic_code}}</td>
                <td>Дата: {{request.request_date}}</td>
                <td>
                  <EditButtonComponent
                      :item="request"
                      label="Редактировать"
                      @edit="openRequestForm"
                  />
                </td>
              </tr>
              <!-- Вторая строка -->
              <tr>
                <td>{{request.request_from_client_company.symbolic_code}}</td>
                <td>{{request.request_responsible_person.symbolic_code}}</td>
                <td colspan="3">Обновлено:
                  {{request.updated_at ? new Date(request.updated_at).toISOString().split('T')[0] : ''}}
                </td>
              </tr>
              </tbody>
            </table>
          </div>
        </li>
      </ul>
    </div>

    <!-- Блок 2: Список строк для выбранного запроса -->
    <ClientRequestLinesComponent
        v-if="showRequestLinesForSelectedItem"
        :request_id="selectedItem_id"
        :key="selectedItem?.value?.id"
        label="Список строк запроса:"
        @close="showRequestLinesForSelectedItem = false"
    />
    <client-request-form
        v-model:showForm="showRequestForm"
        :request_id="request_to_edit_id"
        @data-updated="handleFormSubmit"
        @cancel="closeRequestForm"
    />
  </div>
</template>

<script>
import {ref, computed, onMounted, nextTick} from 'vue';
import axios from "axios";
import {API_URL} from "@/config/api.js";
import AppActionButton from "../../components/AppActionButton.vue"
import ClientRequestForm from './ClientRequestForm.vue'
import EditButtonComponent from "@/pages/client_request/components/EditButtonComponent.vue";
import {DictionaryStore} from "@/services/stores/dictionaryStore.ts";
import ClientRequestLinesComponent from "@/pages/client_request/components/ClientRequestLinesListComponent.vue";

export default {
  name: 'ClientRequest',
  components: {EditButtonComponent, AppActionButton, ClientRequestForm, ClientRequestLinesComponent},
  setup() {
    // Реактивные переменные
    const request_list_items = ref([]);
    const pagination = ref({next: null, previous: null}); // Пагинация
    const request_to_edit_id = ref(false);
    const selectedItem_id = ref(false);
    const isEditMode = ref(false);
    const showRequestForm = ref(false)
    const showRequestLinesForSelectedItem = ref(false)
    const selectedItem = ref(null); // Выбранный элемент
    const isEditFormVisible = ref(false); // Видимость формы редактирования

    // Методы
    const openRequestForm = (request = null) => {
      if (request !== null) {
        request_to_edit_id.value = request.id
        // isEditMode.value = true
      } else {
        // Режим создания
        request_to_edit_id.value = null
        // isEditMode.value = false
      }
      showRequestForm.value = true
    }
    const closeRequestForm = () => {showRequestForm.value = false}
    const handleFormSubmit = async (formData) => {
      closeRequestForm()
      await fetchRequestList()
    }

    // Метод для выбора элемента
    const selectItem = (request) => {
      // console.log('selectItem', request.id)
      if (selectedItem.value?.id === request.id) {
        // Если элемент уже выбран, снимаем выбор
        selectedItem.value = null;
        showRequestLinesForSelectedItem.value = false;
        selectedItem_id.value=null
      } else {
        // Иначе выбираем элемент
        selectedItem.value = request;
        showRequestLinesForSelectedItem.value = true;
        selectedItem_id.value = request.id
      }
    };
    const fetchRequestList = async () => {
      try {
        request_list_items.value = await DictionaryStore.getDictionaryAsAList('ClientRequests', 1);
      } catch (error) {
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
      isEditMode,
      request_to_edit_id,
      openRequestForm,
      closeRequestForm,
      handleFormSubmit,
      selectedItem,
      selectItem,
      pagination,
      fetchRequestList,
      selectedItem_id,
      showRequestLinesForSelectedItem
    };
  }
};
</script>

<style scoped>
/* Добавьте это временно для тестирования */
.modal-class { /* или какой класс использует ваше модальное окно */
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>