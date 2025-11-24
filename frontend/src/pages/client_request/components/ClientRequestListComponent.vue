<template>
  <div class="w3-container w3-light-grey w3-padding">
    <!-- Блок 1: Список запросов клиентов -->
    <div>
<!--      <button @click="openRequestForm(null)"-->
<!--              class="w3-button w3-teal w3-margin-bottom">-->
<!--        <i class="fa fa-plus"></i> Создать новый запрос-->
<!--      </button>-->
      <ul class="w3-ul">
        <li
            v-for="request in requestListItems"
            :key="request.id"
            class="w3-bar"
            :class="{ 'w3-light-blue': selectedItem?.id === request.id }"
            @click="selectItem(request)"
            @dblclick="editSelectedRequest(request)"
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
                      @edit="editSelectedRequest(request)"
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
<!--    <ClientRequestLinesListComponent-->
<!--        v-if="showRequestLinesForSelectedItem"-->
<!--        :requestObject="selectedItem"-->
<!--        label="Список строк запроса:"-->
<!--        @close="showRequestLinesForSelectedItem = false"-->
<!--    />-->
<!--    <client-request-form-->
<!--        v-model:showForm="showRequestForm"-->
<!--        :request_id="request_to_edit_id"-->
<!--        @data-updated="handleFormSubmit"-->
<!--        @cancel="closeRequestForm"-->
<!--    />-->
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue';
import axios from "axios";
import { API_URL } from "@/config/api.js";
import EditButtonComponent from "@/pages/client_request/components/EditButtonComponent.vue";
import { DictionaryStore } from "@/services/stores/dictionaryStore.ts";
import ClientRequestLinesListComponent from "@/pages/client_request/components/ClientRequestLinesListComponent.vue";

// Реактивные состояния
const requestListItems = ref([]);
const selectedItem = ref(null);
const selectedItemId = ref(null);
const showRequestLinesForSelectedItem = ref(false);

const emit = defineEmits(['edit-request', 'update:modelValue']);
// Методы
const fetchRequestList = async () => {
  try {
    requestListItems.value = await DictionaryStore.getDictionaryAsAList('ClientRequests', 1);
  } catch (error) {
    console.error('Error fetching request list:', error);
  }
};

const editSelectedRequest = (request = null) => {
  // console.log('List component editSelectedRequest:', request);
  emit('edit-request', request);
};

const selectItem = (request) => {
  if (selectedItem.value?.id === request.id) {
    // Снятие выбора
    selectedItem.value = null;
    selectedItemId.value = null;
    showRequestLinesForSelectedItem.value = false;
  } else {
    // Выбор элемента
    selectedItem.value = request;
    selectedItemId.value = request.id;
    showRequestLinesForSelectedItem.value = true;
  }
};

// Хук жизненного цикла
onMounted(() => {
  fetchRequestList();
});
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