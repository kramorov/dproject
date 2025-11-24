<template>
  <div class="client-request-lines-list-container">
<!--      <label v-if="label">{{label}}</label>-->

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
                  @edit="openRequestLineEditComponent"
              />
            </td>
          </tr>
          </tbody>
        </table>
      </div>
    </div>
</template>

<script setup>
import EditButtonComponent from "@/pages/client_request/components/EditButtonComponent.vue";

defineOptions({
  name: 'ClientRequestLinesListComponent'
})
import {onMounted, ref, watch} from 'vue';
import {API_URL} from "@/config/api.js";
import axios from "axios";

const props = defineProps({
  requestObject: {
    type: Object,
    default: () => ({}) // Добавляем пустой объект по умолчанию
  }
})

const emit = defineEmits(['edit-line','close']);
const request_line_to_edit_id = ref(false);
const showComponent = ref(false); // Не показывать компонент при ошибке загрузки
const request_lines = ref([]); // Строки для выбранного запроса
    // Загрузка строк для выбранного запроса  client-request-items/?parent_id=2
const fetchRequestLinesList = async (url = `${API_URL}/api/client_requests/client-request-items/`) => {
  if (!props.requestObject?.id) { // Проверяем и selectedItem.value, и его id
    console.error('props.requestObject.id не существует!');
    showComponent.value = false;
    return;
  }
  try {
    const response = await axios.get(url, {
      // params: {selectedItem.value.id }, // Фильтр по выбранному запросу
      params: {parent_id: props.requestObject.id}, // Фильтр по выбранному запросу
    });
    request_lines.value = response.data.results;
    // console.log('request_lines.value', request_lines.value);
    showComponent.value = true
  } catch (error) {
    console.error('ClientRequestLinesListComponent Ошибка загрузки строк запроса:', error);
    showComponent.value = false;
  }

};

const openRequestLineEditComponent = async (line = null) => {
  // console.log('openRequestLineEditComponent request_line_to_edit_id.value',request_line_to_edit_id.value)
    emit('edit-line', line)
};

onMounted(() => {
  if (props.requestObject?.id) {
    fetchRequestLinesList();
  }
});

watch(
  () => props.requestObject?.id, // Добавляем опциональную цепочку
  (newId) => {
    if (newId) {
      fetchRequestLinesList();
    }
  },
  { immediate: true }
);
</script>
