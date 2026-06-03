<!-- pages/RequirementsTest.vue -->
<template>
  <div class="page">
    <RequirementForm type="gearbox" @navigate="onNavigate" />
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import RequirementForm from '@/shared/components/RequirementForm.vue'

const router = useRouter()

function onNavigate({ type, filterParams }) {
  console.log('[RequirementsTest] Navigate with', type, filterParams)
  // TODO: navigate to EngineerSelection page with presetFilters
  alert(`Filter params for ${type}:\n${JSON.stringify(filterParams, null, 2)}`)
}
</script>

<style scoped>
.page { max-width: 1200px; margin: 0 auto; padding: 24px 16px; }
</style>
