<!-- shared/components/catalog/AiPlaceholder.vue — заглушка «AI подбор» -->
<template>
  <div class="ai-placeholder">
    <PageTitle :title="title" subtitle="Опишите задачу — AI подберёт оборудование, параметры и совместимость" />
    <div class="placeholder-body">
      <h2>AI подбор — скоро</h2>
      <p>Опишите вашу задачу на естественном языке, и искусственный интеллект подберёт подходящее оборудование: от арматуры до монтажного комплекта.</p>
    </div>
  </div>
</template>
<script setup>
import { computed } from 'vue'
import Breadcrumbs from '@/shared/components/Breadcrumbs.vue'
import PageTitle from '@/shared/components/PageTitle.vue'
const props = defineProps({
  eqName: { type: String, default: 'Оборудование' },
  labels: { type: Object, default: () => ({}) },
})
defineEmits(['navigate'])
const title = computed(() => props.labels.aiTitle || 'AI подбор')
const eqLabel = computed(() => props.labels.breadcrumbName || props.eqName)
const breadcrumbs = computed(() => [
  { name: 'Каталог', to: '/' },
  { name: eqLabel.value },
  { name: 'AI подбор' },
])
</script>
<style scoped>
.ai-placeholder { max-width: 1200px; margin: 0 auto; padding: var(--cat-gap-xl, 20px); }
.placeholder-body { text-align: center; padding: 80px 20px; }
.placeholder-body h2 { font-size: var(--cat-text-2xl, 24px); font-weight: 600; color: var(--cat-text, #1f2937); margin: 0 0 12px; }
.placeholder-body p { font-size: var(--cat-text-md, 15px); color: var(--cat-muted, #6b7280); max-width: 480px; margin: 0 auto; line-height: 1.6; }
</style>
