<template>
  <div class="client-request-line-edit-container">

    <div class="w3-card-2 w3-padding">
    <TextInputComponent v-model="formData.item_no" :rows="1" label={{}}/>
      <TextInputComponent v-model="formData.request_line_number" :rows="1" label="№ п/п:"/>
    </div>
  </div>
</template>

<script setup>
import EditButtonComponent from "@/pages/client_request/components/EditButtonComponent.vue";
import ClientRequestLinesComponent from "@/pages/client_request/components/ClientRequestLineEditComponent.vue";

defineOptions({
  name: 'ClientRequestLineEditComponent'
})
import {onMounted, ref, toRaw, watch} from 'vue';
import TextInputComponent from "@/pages/client_request/components/TextInputComponent.vue";
import {DictionaryStore} from "@/services/stores/dictionaryStore.ts";


const props = defineProps({
  lineObject: {
    type: Object,
    required: true,
  }
});

const emit = defineEmits(['close']);
const request_line_to_edit_id = ref(false);
const formData = ref({});
const requestItemStructure = ref([])
const ElectricActuatorRequirementStructure= ref([])
const ValveRequirementStructure= ref([])
const ValveSelectionStructure= ref([])
const isLoading = ref(false)

const initializeFormData = async () => {
  // console.log('props.requestObject :', props.requestObject );
  // if (props.requestObject.id === null) {
  //   formData.value.id = null
  //   formData.value.symbolic_code = ''
  //   formData.value.request_type = null
  //   formData.value.request_from_client_company = null
  //   formData.value.request_responsible_person = null
  //   formData.value.end_customer = ''
  //   formData.value.request_date = new Date().toISOString().split('T')[0]
  //   formData.value.request_text = ''
  //   isEditMode.value = false
  // } else {
    formData.value = JSON.parse(JSON.stringify(toRaw(props.lineObject)));
    console.log('formData."symbolic_code":  :', formData.value);
    // formData.value.request_date = props.requestObject.request_date || new Date().toISOString().split('T')[0]
    // formData.value.request_status = getSafeId(formData.value.request_status, 1)
    // formData.value.request_type = getSafeId(formData.value.request_type, 4)
    // formData.value.request_from_client_company = getSafeId(formData.value.request_from_client_company)
    // formData.value.request_responsible_person = getSafeId(formData.value.request_responsible_person)
    // isEditMode.value = true
    // console.log('formData."symbolic_code":  :', formData.value.symbolic_code);
  // }
};
const loadDictionaries = async () => {
  isLoading.value = true
  try {
    [requestItemStructure.value, ElectricActuatorRequirementStructure.value, ValveRequirementStructure.value, ValveSelectionStructure.value] = await Promise.all([
      DictionaryStore.getDictionaryStructure('ClientRequestItem'),
      DictionaryStore.getDictionaryStructure('ElectricActuatorRequirement'),
      DictionaryStore.getDictionaryStructure('ValveRequirement'),
      DictionaryStore.getDictionaryStructure('ValveSelection')
    ])
  } catch (error) {
    console.error('ClientRequestLineEditComponent Ошибка загрузки справочников:', error)
  } finally {
    isLoading.value = false
    console.log('ClientRequestLineEditComponent requestItemStructure.value:', requestItemStructure.value)
  }
};

// Lifecycle hooks
onMounted(async () => {
  console.log('loadDictionaries begin')
  await loadDictionaries()
  console.log('loadDictionaries END')
});

watch(
    () => props.lineObject?.id,
    (newId) => {
      if (newId) {
         console.log('WATCH begin')
        initializeFormData();
        // ClientRequestItem.value.request_line_text
        // requestItemStructure.value.request_line_text
        // let foundObject=getFieldBy(requestItemStructure.value,'name','request_line_text')
        // Существующее поле
        console.log('ClientRequestLineEditComponent foundObject', DictionaryStore.getModelStructureField('ClientRequestItem', 'request_line_text'))
        // console.log('ClientRequestLineEditComponent requestItemStructure.value',requestItemStructure.value )
      }
      console.log('WATCH END')
    },
    {immediate: true}
);
</script>
