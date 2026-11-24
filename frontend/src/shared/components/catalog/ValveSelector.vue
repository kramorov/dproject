<!-- shared/components/catalog/ValveSelector.vue -->
<!-- Переиспользуемый селектор модели арматуры: производитель → серия → тип номенклатуры.
     НЕ фильтр: выбор конкретной модели арматуры, который используется точечным подбором
     (привязка таблицы коэффициентов) и другими местами. -->
<template>
  <div class="valve-selector">
    <label class="valve-selector__field">
      <span class="valve-selector__label">{{ t('pa.engineerPointwise.valveProducer') }}</span>
      <select :value="model.producer_id" @change="onProducerChange($event.target.value)">
        <option value="">{{ '—' }}</option>
        <option v-for="p in producersWithSeries" :key="p.id" :value="p.id">{{ p.name }}</option>
      </select>
    </label>
    <label class="valve-selector__field">
      <span class="valve-selector__label">{{ t('pa.engineerPointwise.valveSeries') }}</span>
      <select :value="model.series_id" :disabled="!model.producer_id" @change="onSeriesChange($event.target.value)">
        <option value="">{{ '—' }}</option>
        <option v-for="s in seriesByProducer" :key="s.id" :value="s.id">{{ s.name || s.code }}</option>
      </select>
    </label>
    <label class="valve-selector__field">
      <span class="valve-selector__label">{{ t('pa.engineerPointwise.valveType') }}</span>
      <select :value="model.valve_type_id" @change="onValveTypeChange($event.target.value)">
        <option value="">{{ '—' }}</option>
        <option v-for="vt in valveTypes" :key="vt.id" :value="vt.id">{{ vt.name }}</option>
      </select>
    </label>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from '@/shared/i18n'

const { t } = useI18n()

const props = defineProps({
  producers: { type: Array, default: () => [] },
  series: { type: Array, default: () => [] },
  valveTypes: { type: Array, default: () => [] },
  modelValue: { type: Object, default: () => ({ producer_id: '', series_id: '', valve_type_id: '' }) },
})

const emit = defineEmits(['update:modelValue'])

// Локальный доступ к v-model (в шаблоне обращаемся как model.*).
const model = computed(() => props.modelValue)

// Производители — только те, у кого есть серии арматуры.
const producersWithSeries = computed(() => {
  const ids = new Set((props.series || []).map(s => s.valve_producer_id).filter(Boolean))
  return (props.producers || []).filter(p => ids.has(p.id))
})

const seriesByProducer = computed(() => {
  if (!props.modelValue.producer_id) return []
  return (props.series || []).filter(s => s.valve_producer_id === props.modelValue.producer_id)
})

function toId(v) {
  return v === '' || v == null ? '' : Number(v)
}

function onProducerChange(v) {
  // Смена производителя — сброс серии и типа.
  emit('update:modelValue', { producer_id: toId(v), series_id: '', valve_type_id: '' })
}

function onSeriesChange(v) {
  const s = (props.series || []).find(x => x.id === toId(v))
  emit('update:modelValue', {
    producer_id: props.modelValue.producer_id,
    series_id: toId(v),
    // При выборе серии подставляем тип номенклатуры (из привязанной таблицы коэффициентов).
    valve_type_id: (s && s.valve_type_id) || '',
  })
}

function onValveTypeChange(v) {
  emit('update:modelValue', { ...props.modelValue, valve_type_id: toId(v) })
}
</script>

<style scoped>
.valve-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-end;
  background: var(--cat-bg, #fff);
  border: 1px solid var(--cat-border, #e5e7eb);
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 16px;
}
.valve-selector__field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 180px;
  flex: 1 1 200px;
}
.valve-selector__label {
  font-size: var(--cat-text-xs, 12px);
  color: var(--cat-muted, #6b7280);
}
.valve-selector select {
  padding: 6px 8px;
  border: 1px solid var(--cat-border, #e5e7eb);
  border-radius: 6px;
  font-size: var(--cat-text-base, 14px);
  background: var(--cat-surface, #fff);
  color: var(--cat-text, #1f2937);
}
.valve-selector select:disabled {
  background: var(--cat-bg, #f3f4f6);
  color: var(--cat-muted-light, #9ca3af);
  cursor: not-allowed;
}
</style>
