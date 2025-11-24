<script setup>
import {ref} from 'vue';
import ClientRequestListComponent from "@/pages/client_request/components/ClientRequestListComponent.vue";
import ClientRequestEditComponent from "@/pages/client_request/components/ClientRequestEditComponent.vue";
import ClientRequestLineEditComponent from "@/pages/client_request/components/ClientRequestLineEditComponent.vue";

const currentStep = ref('request_list');
const requestToEdit = ref(null);
const requestLineToEdit = ref(null);

function openRequestEditComponent(request) {
  requestToEdit.value = request;
  currentStep.value = 'request';
  // console.log('MAIN component editSelectedRequest:', request);
}

function openRequestLine(line) {
  // console.log('FROM MAIN openRequestLine started, line', line);
  requestLineToEdit.value = line;
  currentStep.value = 'line';
}

function back() {
  currentStep.value = currentStep.value === 'line' ? 'request' : 'request_list';
}
</script>

<template>
  <div class="w3-container w3-light-grey w3-padding">
    <ClientRequestListComponent
        v-if="currentStep === 'request_list'"
        @edit-request="openRequestEditComponent"
    />
    <ClientRequestEditComponent
        v-else-if="currentStep === 'request'"
        :requestObject="requestToEdit"
        @back="back"
        @data-updated="back"
        @edit-line="openRequestLine"
    />
    <ClientRequestLineEditComponent
        v-else-if="currentStep === 'line'"
        :lineObject="requestLineToEdit"
        @back="back"
    />
  </div>
</template>