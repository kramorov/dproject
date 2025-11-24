<template>
  <div class="client-request-edit-container">
    <div class="w3-container w3-light-grey w3-padding w3-small">
      <h2>{{title}}</h2>
      <!-- Основная информация -->
      <div class="w3-row-padding ">
        <div class="w3-quarter ">
          <label>Дата запроса</label>
          <input v-model="formData.request_date" class="w3-input w3-border w3-small" type="date" required>
        </div>
        <div class="w3-quarter">
          <SelectDropDownComponent
              v-model="formData.request_status"
              :options="dataStore.requestStatusTable"
              label="Статус"
              required
          />
        </div>
        <div class="w3-half">
          <SelectDropDownComponent
              v-model="formData.request_type"
              :options="dataStore.requestTypesTable"
              label="Тип запроса"
              required
          />
        </div>
      </div><!--            Конец основной информации-->
      <!--            название запроса-->
      <TextInputComponent v-model="formData.symbolic_code" :rows="1" label="Название запроса:"/>
      <!--            Блок название заказчика и ответственное лицо заказчика-->
      <div class="w3-row-padding ">
        <div v-if="!dataStore.isLoading">
          <div class="w3-half">
            <SelectDropDownComponent
                v-model="formData.request_from_client_company"
                :options="dataStore.companiesTable"
                label="Компания-заказчик"
                @change="updateEmployees"
                required
            />
          </div>
          <div class="w3-half w3-row-padding">
            <SelectDropDownComponent
                v-model="formData.request_responsible_person"
                :options="employeesTable"
                label="Ответственное лицо"
                :disabled="!formData.request_from_client_company"
                required
            />
          </div>
        </div>
      </div>
      <TextInputComponent v-model="formData.end_customer" :rows="1" label="Конечный потребитель:"/>
      <TextInputComponent v-model="formData.request_text" :rows="5" label="Текст запроса:"/>
      <ClientRequestLinesListComponent
          :requestObject="props.requestObject"
          @edit-line="openRequestLineFromChild"
          label="Список строк запроса:"
      />
      <!-- Футер с кнопками -->
      <footer class="w3-container w3-padding w3-light-grey w3-bottomright">
        <button type="submit" class="w3-button w3-padding w3-teal w3-margin-right" @click="handleSubmit">
          {{isEditMode ? 'Обновить запрос' : 'Создать запрос'}}
        </button>
        <!--                <button type="button" class="w3-button w3-padding w3-red" @click="handleCancel">Отмена</button>-->
        <button type="button" class="w3-button w3-padding w3-red" @click="emit('back')">Назад к списку запросов</button>
      </footer>
    </div>
  </div>

</template>
<script setup>
import {computed, onMounted, ref, toRaw, watch} from 'vue'
import {DictionaryStore} from "@/services/stores/dictionaryStore.ts"
import {useDataStore} from '@/services/store.js'
import SelectDropDownComponent from "@/pages/client_request/components/SelectDropDownComponent.vue"
import TextInputComponent from "@/pages/client_request/components/TextInputComponent.vue";
import axios from "axios";
import ClientRequestLinesListComponent from "@/pages/client_request/components/ClientRequestLinesListComponent.vue";

defineOptions({
  name: 'ClientRequestEditComponent'
})

const props = defineProps({
  requestObject: {
    type: Object,
    required: true
  }
})
const isEditMode = ref(false)
const emit = defineEmits(['submit', 'back', 'cancel', 'data-updated','edit-line'])
// Stores
const dataStore = useDataStore()

// Reactive state
const formData = ref({})
const requestTypesTable = ref([])
const requestStatusTable = ref([])
const companiesTable = ref([])
const employeesTable = ref([])
const isLoading = ref(false)

// Computed
const title = computed(() =>
    isEditMode ? "Редактирование запроса" : "Создание нового запроса"
)
const openRequestLineFromChild = async (line = null) => {
    emit('edit-line', line) // Пробрасываем событие выше
};

// Utility functions
const getSafeId = (value, defaultValue = null) => {
  return value === null || value === undefined
      ? defaultValue
      : typeof value === 'object' ? value?.id : value
}

const updateEmployees = () => {
  if (dataStore.isLoading) return
  const selectedCompany = dataStore.companiesTable.find(
      c => c.id === formData.value.request_from_client_company
  )

  employeesTable.value = selectedCompany?.employees || []
  const currentEmployeeId = formData.value.request_responsible_person
  const hasCurrentEmployee = employeesTable.value.some(e => e.id === currentEmployeeId)

  formData.value.request_responsible_person = hasCurrentEmployee
      ? currentEmployeeId
      : employeesTable.value.length === 1 ? employeesTable.value[0].id : null
}

const validateForm = () => {
  if (!formData.value.request_type) {
    alert('Выберите тип запроса')
    return false
  }
  return true
}

const loadDictionaries = async () => {
  isLoading.value = true
  try {
    [requestTypesTable.value, requestStatusTable.value, companiesTable.value, employeesTable.value] = await Promise.all([
      DictionaryStore.getDictionary('ClientRequestsType'),
      DictionaryStore.getDictionary('ClientRequestsStatus'),
      DictionaryStore.getDictionary('Company'),
      DictionaryStore.getDictionary('CompanyPerson')
    ])
  } catch (error) {
    console.error('Ошибка загрузки справочников:', error)
  } finally {
    isLoading.value = false
  }
}

const initializeFormData = async () => {
  // console.log('props.requestObject :', props.requestObject );
  if (props.requestObject.id === null) {
    formData.value.id = null
    formData.value.symbolic_code = ''
    formData.value.request_type = null
    formData.value.request_from_client_company = null
    formData.value.request_responsible_person = null
    formData.value.end_customer = ''
    formData.value.request_date = new Date().toISOString().split('T')[0]
    formData.value.request_text = ''
    isEditMode.value = false
  } else {
    // formData.value = await DictionaryStore.getDictionaryItemById('ClientRequests', props.request_id)
    // formData.value.request_date = formData.value.request_date || new Date().toISOString().split('T')[0]
    // formData.value.request_status = getSafeId(formData.value.request_status, 1)
    // formData.value.request_type = getSafeId(formData.value.request_type, 4)
    // formData.value.request_from_client_company = getSafeId(formData.value.request_from_client_company)
    // formData.value.request_responsible_person = getSafeId(formData.value.request_responsible_person)
    formData.value = JSON.parse(JSON.stringify(toRaw(props.requestObject)));
    formData.value.request_date = props.requestObject.request_date || new Date().toISOString().split('T')[0]
    formData.value.request_status = getSafeId(formData.value.request_status, 1)
    formData.value.request_type = getSafeId(formData.value.request_type, 4)
    formData.value.request_from_client_company = getSafeId(formData.value.request_from_client_company)
    formData.value.request_responsible_person = getSafeId(formData.value.request_responsible_person)
    isEditMode.value = true
    // console.log('formData."symbolic_code":  :', formData.value.symbolic_code);
    updateEmployees()
  }
}
const saveRequest = async () => {
  const r_data = JSON.parse(JSON.stringify(formData.value));
  const isUpdate = !!formData.value.id;
  const url = isUpdate
      ? `/api/client_requests/clientrequestlist/${formData.value.id}/`
      : '/api/client_requests/clientrequestlist/';
  // console.log(r_data,isUpdate,url)
  try {
    // console.log(isUpdate ? 'Обновление запроса:' : 'Создание запроса:', r_data);
    const response = isUpdate
        ? await axios.patch(url, r_data)
        : await axios.post(url, r_data);

    return response.data;

  } catch (error) {
    console.error(`Ошибка при ${isUpdate ? 'обновлении' : 'создании'} запроса:`, error);

    const errorMessage = error.response?.data
        ? `Ошибка: ${JSON.stringify(error.response.data)}`
        : `Произошла ошибка при ${isUpdate ? 'обновлении' : 'создании'} запроса`;

    alert(errorMessage);
    throw error; // Пробрасываем ошибку дальше, если нужно
  }
};

// Использование:
const handleSubmit = async () => {
  try {
    await saveRequest();
    // Дополнительные действия после успешного сохранения
    emit('data-updated', false)
  } catch {
    // Обработка ошибки (опционально)
  }
};

const handleCancel = async () => {
  emit('cancel', false)
};
// Lifecycle hooks
onMounted(async () => {
  await loadDictionaries()
})
// Watcher с deep-отслеживанием
watch(
  () => props.requestObject?.id,
  (newRequestObject) => {
    // console.log('watched newRequestObject change:', newRequestObject, props.requestObject)
    initializeFormData()
  },
  { deep: true, immediate: true } // Добавляем эти опции
)
</script>

<style>


</style>