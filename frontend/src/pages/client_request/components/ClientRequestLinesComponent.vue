<template>
  <div class="client-request-lines-container">
    <div v-if="showComponent">
      <label v-if="label">{{label}}</label>

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
            <td>{{line.item_no}}</td>
            <td>{{line.request_line_number}}</td>
            <td>{{line.request_line_ol}}</td>
            <td>{{line.valve_requirement.valve_requirement_text_description}}</td>
            <td>
              <EditButtonComponent
                  :item="line"
                  label="Редактировать"
                  @edit="openRequestLineForm"
              />
            </td>
          </tr>
          </tbody>
        </table>
      </div>
      <request-line-edit-form
        v-model:showForm="showRequestLineEditComponent"
        :request_id="request_to_edit_id"
        @data-updated="handleFormSubmit"
        @cancel="closeRequestForm"
    />
    </div>
  </div>
</template>

<script setup>
import EditButtonComponent from "@/pages/client_request/components/EditButtonComponent.vue";

defineOptions({
  name: 'ClientRequestLinesComponent'
})
import {ref, watch} from 'vue';
import {API_URL} from "@/config/api.js";
import axios from "axios";
import ClientRequestForm from "@/pages/client_request/ClientRequestForm.vue";

const props = defineProps({
  request_id: null,
  label: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['close']);
const request_line_to_edit_id = ref(false);
const showComponent = ref(false);
const request_lines = ref([]); // Строки для выбранного запроса
const showRequestLineEditComponent = ref(false);
    // Загрузка строк для выбранного запроса  client-request-items/?parent_id=2
const fetchRequestLines = async (url = `${API_URL}/api/client_requests/client-request-items/`) => {
  if (!props.request_id) { // Проверяем и selectedItem.value, и его id
    console.error('props.request_id не существует!');
    showComponent.value = false;
    return;
  }
  try {
    const response = await axios.get(url, {
      // params: {selectedItem.value.id }, // Фильтр по выбранному запросу
      params: {parent_id: props.request_id}, // Фильтр по выбранному запросу
    });
    request_lines.value = response.data.results;
    showComponent.value = true
  } catch (error) {
    showComponent.value = false;
  }

};
const openRequestLineEditComponent = (line = null) => {
  if (line !== null) {
    request_line_to_edit_id.value = line.id
    // isEditMode.value = true
  } else {
    // Режим создания
    request_line_to_edit_id.value = null
    // isEditMode.value = false
  }
  showRequestLineEditComponent.value = true
}
// watch(
//   () => props.request_id,
//   (newId) => {
//     if (newId) {
//       fetchRequestLines();
//     }
//   },
//   { immediate: true }
// );
</script>
