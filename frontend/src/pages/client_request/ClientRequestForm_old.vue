<template>
<!--  <div class="w3-modal" style="display: block" @click.self="closeForm">-->
  <div class="w3-modal">
<!--    <div class="w3-modal-content w3-card-3 w3-animate-opacity" style="max-width: 95%">-->
    <div class="w3-modal-content w3-card-4">
      <div class="w3-container w3-light-grey w3-padding w3-small">
        <!-- Индикатор загрузки -->
        <div v-if="dataStore.isLoading" class="w3-container w3-center w3-padding-24">
          <div class="w3-spinner w3-large"></div>
          <p>Загрузка данных...</p>
        </div>

        <!-- Сообщение об ошибке -->
        <div v-else-if="dataStore.error" class="w3-container w3-center w3-padding-24 w3-red">
          <p>Ошибка загрузки: {{dataStore.error}}</p>
<!--          <button @click="dataStore.fetchInitialData()" class="w3-button w3-white">-->
<!--            Повторить попытку-->
<!--          </button>-->
        </div>
        <!-- Основная форма запроса -->
        <div class="w3-card w3-padding">
          <h2>{{title}}</h2>

<!--          <form @submit.prevent="submitForm">-->
<!--            &lt;!&ndash; Основная информация &ndash;&gt;-->
<!--            <div class="w3-row-padding w3-margin-bottom">-->
<!--              <div class="w3-third">-->
<!--                <label>Дата запроса</label>-->
<!--                <input v-model="formData.request_date" class="w3-input w3-border w3-small" type="date" required>-->
<!--              </div>-->
<!--              <div class="w3-third">-->
<!--                &lt;!&ndash;                <label>Статус</label>&ndash;&gt;-->
<!--                &lt;!&ndash;                <select v-model="formData.request_status" class="w3-select w3-border w3-small w3-light-gray" required>&ndash;&gt;-->
<!--                &lt;!&ndash;                  <option v-for="type in requestStatusTable" :key="type.id" :value="type.id">&ndash;&gt;-->
<!--                &lt;!&ndash;                    {{type.text_description}}&ndash;&gt;-->
<!--                &lt;!&ndash;                  </option>&ndash;&gt;-->
<!--                &lt;!&ndash;                </select>&ndash;&gt;-->
<!--                <SelectDropDownComponent-->
<!--                    v-model="formData.request_status"-->
<!--                    :options="dataStore.requestStatusTable"-->
<!--                    label="Статус"-->
<!--                    required-->
<!--                />-->
<!--              </div>-->
<!--              <div class="w3-third">-->
<!--                &lt;!&ndash;                <label>Тип запроса</label>&ndash;&gt;-->
<!--                &lt;!&ndash;                <select v-model="formData.request_type" class="w3-select w3-border w3-small w3-teal" required>&ndash;&gt;-->
<!--                &lt;!&ndash;                  <option v-for="type in requestTypesTable" :key="type.id" :value="type.id">&ndash;&gt;-->
<!--                &lt;!&ndash;                    {{type.symbolic_code}}&ndash;&gt;-->
<!--                &lt;!&ndash;                  </option>&ndash;&gt;-->
<!--                &lt;!&ndash;                </select>&ndash;&gt;-->
<!--                <SelectDropDownComponent-->
<!--                    v-model="formData.request_type"-->
<!--                    :options="dataStore.requestTypesTable"-->
<!--                    label="Тип запроса"-->
<!--                    required-->
<!--                />-->
<!--              </div>-->
<!--            </div>-->
<!--            <div class="w3-row w3-margin-bottom">-->
<!--              <div class="w3-col" style="width:120px">-->
<!--                <label class="w3-padding-small">Название запроса:</label>-->
<!--              </div>-->
<!--              <div class="w3-rest">-->
<!--                <textarea-->
<!--                    v-model="formData.symbolic_code"-->
<!--                    class="w3-input w3-border"-->
<!--                    rows="1"-->
<!--                ></textarea>-->
<!--              </div>-->
<!--            </div>-->
<!--            <div class="w3-row-padding w3-margin-bottom">-->
<!--              <div v-if="!dataStore.isLoading">-->
<!--                <div class="w3-half">-->
<!--                  <SelectDropDownComponent-->
<!--                      v-model="formData.request_from_client_company"-->
<!--                      :options="dataStore.companiesTable"-->
<!--                      label="Компания-заказчик"-->
<!--                      @change="updateEmployees"-->
<!--                      required-->
<!--                  />-->
<!--                </div>-->
<!--                <div class="w3-half">-->
<!--                  &lt;!&ndash;                  <SelectDropDownComponent&ndash;&gt;-->
<!--                  &lt;!&ndash;                    v-model="formData.request_responsible_person"&ndash;&gt;-->
<!--                  &lt;!&ndash;                    :options="employeesTable"&ndash;&gt;-->
<!--                  &lt;!&ndash;                    label="Ответственное лицо"&ndash;&gt;-->
<!--                  &lt;!&ndash;                    :disabled="!formData.request_from_client_company"&ndash;&gt;-->
<!--                  &lt;!&ndash;                    required&ndash;&gt;-->
<!--                  &lt;!&ndash;                  />&ndash;&gt;-->
<!--                  <label>Ответственное лицо</label>-->
<!--                  &lt;!&ndash;                <input v-model="formData.request_responsible_person" class="w3-input w3-border" type="text" required>&ndash;&gt;-->
<!--                  <select v-model="formData.request_responsible_person" class="w3-select w3-border w3-small w3-teal"-->
<!--                          :disabled="!formData.request_from_client_company" required>-->
<!--                    <option v-for="employee in employeesTable" :key="employee.id" :value="employee.id">-->
<!--                      {{employee.symbolic_code}}-->
<!--                    </option>-->
<!--                  </select>-->
<!--                </div>-->
<!--              </div>-->
<!--            </div>-->
<!--            <div class="w3-row w3-margin-bottom">-->
<!--              <div class="w3-col" style="width:120px">-->
<!--                <label class="w3-padding-small">Конечный потребитель:</label>-->
<!--              </div>-->
<!--              <div class="w3-rest">-->
<!--                <textarea-->
<!--                    v-model="formData.end_customer"-->
<!--                    class="w3-input w3-border"-->
<!--                    rows="1"-->
<!--                ></textarea>-->
<!--              </div>-->
<!--            </div>-->

<!--            <div class="w3-margin-bottom">-->
<!--              <label>Текст запроса</label>-->
<!--              <textarea v-model="formData.request_text" class="w3-input w3-border" rows="3"></textarea>-->
<!--            </div>-->


            <!--            <button type="button" @click="addItem" class="w3-button w3-blue w3-margin-top">-->
            <!--              Добавить позицию-->
            <!--            </button>-->
                  <!-- Футер с кнопками -->
            <footer class="w3-container w3-padding w3-light-grey">
              <button class="w3-button w3-padding w3-teal " @click="submitForm">{{isEditMode ? 'Обновить запрос' : 'Создать запрос'}}</button>
              <button class="w3-button w3-padding w3-red" @click="cancel">Отмена</button>
            </footer>
<!--            <div class="w3-margin-top">-->
<!--&lt;!&ndash;              <button type="submit" class="w3-button w3-green">&ndash;&gt;-->
<!--&lt;!&ndash;                {{isEditMode ? 'Обновить запрос' : 'Создать запрос'}}&ndash;&gt;-->
<!--&lt;!&ndash;              </button>&ndash;&gt;-->
<!--&lt;!&ndash;              <button type="button" @click="cancel" class="w3-button w3-red w3-right">&ndash;&gt;-->
<!--&lt;!&ndash;                Отмена&ndash;&gt;-->
<!--&lt;!&ndash;              </button>&ndash;&gt;-->
<!--            </div>-->
<!--          </form>-->
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import {computed, onMounted, ref} from 'vue'
import {API_URL} from "@/config/api.js"
import axios from "axios"
import {useDataStore} from '@/services/store.js'
import {storeToRefs} from 'pinia'
import SelectDropDownComponent from './components/SelectDropDownComponent.vue';

const props = defineProps({
  initialData: {
    type: Object,
    default: () => ({
      request_date: '',
      request_status: null,
      request_type: null,
      end_customer: '',
      request_from_client_company: null,
      request_responsible_person: null,
      request_text: '',
      items: []
    })
  },
  isEditMode: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['submit', 'cancel'])
const title = computed(() =>
    props.isEditMode ? "Редактирование запроса" : "Создание нового запроса"
);
// Подгружаем нужные справочники
const dataStore = useDataStore()
// Используем storeToRefs для деструктуризации с сохранением реактивности
const {companiesTable, requestTypesTable, requestStatusTable, companiesCount} = storeToRefs(dataStore)
// Получаем метод из store


// Реактивные данные
const formData = ref(JSON.parse(JSON.stringify(props.initialData)))
// const requestTypesTable = ref([])
// const requestStatusTable = ref([])
// const companiesTable = ref([])
const employeesTable = ref([])
const valveTypes = ref([])
const pressureUnits = ref([])
const ipRatings = ref([])
const exdTypes = ref([])
const temperatureRanges = ref([])
const timeUnits = ref([])
const operatingModes = ref([])
const dictionariesLoaded = ref(false);

// Методы
const updateEmployees = () => {
  // Находим выбранную компанию по ID из formData
  if (!dataStore.isLoading) {
    const selectedCompany = [...dataStore.companiesTable].find(
        company => company.id === formData.value.request_from_client_company
    );
    // console.log('selectedCompany', selectedCompany)
    // Получаем сотрудников выбранной компании или пустой массив
    const companyEmployees = selectedCompany?.employees || [];
    // console.log('companyEmployees', companyEmployees)
    // Обновляем список доступных сотрудников
    employeesTable.value = companyEmployees;
    const currentSelected = companyEmployees.find(emp => emp.id === formData.value.request_responsible_person);
    if (currentSelected) {
      formData.value.request_responsible_person = currentSelected.id;
    } else {
      formData.value.request_responsible_person = companyEmployees.length === 1
          ? companyEmployees[0].id
          : null;
    }
  }
}
// const loadDictionaries = async () => {
//   try {
//     const [companiesRes, requestTypesRes, requestStat] = await Promise.all([
//       axios.get(`${API_URL}/api/clients/companies-list/`),
//       axios.get(`${API_URL}/api/client_requests/clientrequesttypelist/`),
//       axios.get(`${API_URL}/api/client_requests/client-requests-status/`)
//     ])
//     companiesTable.value = companiesRes.data.results
//     requestTypesTable.value = requestTypesRes.data.results
//     requestStatusTable.value = requestStat.data.results
//     // Заглушки для демонстрации
//     valveTypes.value = [
//       {id: 1, symbolic_code: 'ЗК', text_description: 'Задвижка клиновая'},
//       {id: 2, symbolic_code: 'КШ', text_description: 'Кран шаровый'}
//     ]
//
//     ipRatings.value = [
//       {id: 1, symbolic_code: 'IP54', text_description: 'IP54'},
//       {id: 2, symbolic_code: 'IP65', text_description: 'IP65'}
//     ]
//     dictionariesLoaded.value = true;
//
//   } catch (error) {
//     console.error('Ошибка загрузки справочников:', error)
//   }
//   updateEmployees();
// }
const validateForm = () => {
  if (!formData.value.request_type) {
    alert('Выберите тип запроса')
    return false
  }
  return true
}

const submitForm = () => {
  console.log('submitForm');
  if (!validateForm()) return
  const dataToSend = JSON.parse(JSON.stringify(formData.value))
  emit('submit', dataToSend)
}

const cancel = () => {
  console.log('cancel');
  emit('cancel')
}

const closeForm = () => {
  console.log('closeForm');

}


const {fetchInitialData} = dataStore

// Функция для обновления данных
const fetchData = async () => {
  await fetchInitialData();
  console.log('После fetchData isLoading=', dataStore.isLoading);
};
// Хуки жизненного цикла
onMounted(async () => {
      // await fetchInitialData();
      // console.log('После mount isLoading=', dataStore.isLoading);
      // // Устанавливаем дату по умолчанию, если она пустая или undefined
      // formData.value.request_date = formData.value.request_date || new Date().toISOString().split('T')[0];
      //
      // // Функция для безопасного получения ID из объекта или значения
      // const getSafeId = (value, defaultValue) => {
      //   if (value === null || value === undefined) return defaultValue;
      //   return typeof value === 'object' ? value?.id : value;
      // };
      //
      // // Устанавливаем значения с проверками
      // formData.value.request_status = getSafeId(formData.value.request_status, 1);
      // formData.value.request_type = getSafeId(formData.value.request_type, 4);
      //
      // // Получаем ID из initialData или null
      // formData.value.request_from_client_company = props.initialData?.request_from_client_company?.id || null;
      // formData.value.request_responsible_person = props.initialData?.request_responsible_person?.id || null;
      //
      // updateEmployees();
      // console.log('mount request_from_client_company=', formData.value.request_from_client_company);
    }
)
</script>

<style scoped>
  .w3-modal {
    z-index: 1000;
    display: block !important;
  }
</style>