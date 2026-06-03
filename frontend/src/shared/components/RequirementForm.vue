<!-- shared/components/RequirementForm.vue -->
<!-- Dynamic form for equipment requirements. Fetches schema, renders fields, calls preview API. -->
<template>
  <div class="req-form">
    <div class="req-form__header">
      <h2 class="req-form__title">{{ schema?.label || 'Требования' }}</h2>
      <select v-model="selectedType" class="req-form__type-select" @change="loadSchema">
        <option v-for="t in TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
      </select>
    </div>

    <div v-if="loading" class="req-form__loading">Загрузка...</div>

    <form v-else-if="schema" class="req-form__fields" @submit.prevent="onSubmit">
      <!-- Exd cascade — special field rendered outside schema loop -->
      <div v-if="hasExdField" class="req-form__field">
        <label>Взрывозащита</label>
        <ExdFilter
          single
          @update:modelValue="val => exdValue = val"
        />
      </div>

      <!-- Regular fields from schema -->
      <div v-for="f in nonExdFields" :key="f.name" class="req-form__field">
        <label :for="'rf-'+f.name">{{ f.label }}</label>

        <!-- FK select -->
        <select
          v-if="f.field_type === 'fk'"
          :id="'rf-'+f.name"
          v-model="formData[f.name]"
        >
          <option :value="null">{{ f.optional ? '—' : 'Выберите...' }}</option>
          <option v-for="c in f.choices" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>

        <!-- Integer / Decimal -->
        <input
          v-else-if="f.field_type === 'integer' || f.field_type === 'decimal'"
          :id="'rf-'+f.name"
          type="number"
          :step="f.field_type === 'decimal' ? '0.01' : '1'"
          v-model.number="formData[f.name]"
          :placeholder="f.label"
        />

        <!-- Boolean -->
        <input
          v-else-if="f.field_type === 'boolean'"
          :id="'rf-'+f.name"
          type="checkbox"
          v-model="formData[f.name]"
        />

        <!-- String / fallback -->
        <input
          v-else
          :id="'rf-'+f.name"
          type="text"
          v-model="formData[f.name]"
          :placeholder="f.label"
        />
      </div>

      <div class="req-form__actions">
        <button type="submit" class="req-form__btn req-form__btn--primary" :disabled="previewLoading">
          {{ previewLoading ? 'Поиск...' : 'Подобрать оборудование' }}
        </button>
        <button type="button" class="req-form__btn" @click="resetForm">Сбросить</button>
      </div>
    </form>

    <div v-if="previewResult" class="req-form__result">
      Найдено параметров: <code>{{ JSON.stringify(previewResult.filter_params) }}</code>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import api from '@/shared/api'
import ExdFilter from '@/shared/components/ExdFilter.vue'

const TYPES = [
  { value: 'gearbox', label: 'Редуктор' },
  { value: 'filter_regulator', label: 'Фильтр-регулятор' },
  { value: 'limit_switch', label: 'БКВ' },
]

const props = defineProps({
  type: { type: String, default: 'gearbox' },
})

const emit = defineEmits(['navigate'])

const selectedType = ref(props.type)
const schema = ref(null)
const loading = ref(false)
const previewLoading = ref(false)
const previewResult = ref(null)
const formData = reactive({})
const exdValue = ref(null)

const hasExdField = computed(() =>
  schema.value?.fields?.some(f => f.name === 'exd_protection')
)

const nonExdFields = computed(() =>
  schema.value?.fields?.filter(f => f.name !== 'exd_protection') || []
)

watch(() => props.type, (val) => {
  selectedType.value = val
  loadSchema()
})

onMounted(() => loadSchema())

async function loadSchema() {
  loading.value = true
  previewResult.value = null
  resetForm()
  try {
    const { data } = await api.get('/client_requests/requirements/schema/', {
      params: { type: selectedType.value },
    })
    schema.value = data
  } catch (e) {
    console.error('[RequirementForm] Schema load failed', e)
  }
  loading.value = false
}

function resetForm() {
  for (const k of Object.keys(formData)) {
    delete formData[k]
  }
  exdValue.value = null
}

async function onSubmit() {
  previewLoading.value = true
  try {
    const payload = { type: selectedType.value, ...formData }

    // Map ExdFilter single value to backend field
    if (hasExdField.value) {
      if (exdValue.value === '_none_') {
        // Общепромышленное — no exd filter needed, pass as sentinel
        payload.exd_protection = null
        payload.exd_id_override = '_none_'
      } else if (exdValue.value && typeof exdValue.value === 'number') {
        payload.exd_protection = exdValue.value
      }
      // else: null = no filter
    }

    const { data } = await api.post('/client_requests/requirements/preview/', payload)
    previewResult.value = data
    emit('navigate', {
      type: selectedType.value,
      filterParams: data.filter_params,
    })
  } catch (e) {
    console.error('[RequirementForm] Preview failed', e)
  }
  previewLoading.value = false
}
</script>

<style scoped>
.req-form {
  max-width: 640px;
  margin: 0 auto;
  padding: var(--cat-gap-xl, 16px);
}
.req-form__header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 24px;
}
.req-form__title {
  margin: 0;
  font-size: var(--cat-text-xl, 20px);
  font-weight: 700;
  color: var(--cat-text, #1f2937);
}
.req-form__type-select {
  padding: 8px 12px;
  font-size: var(--cat-text-base, 14px);
  border: 1px solid var(--cat-border, #d1d5db);
  border-radius: var(--cat-radius-md, 6px);
  background: var(--cat-surface, #fff);
}
.req-form__loading {
  text-align: center;
  padding: 32px;
  color: var(--cat-muted, #6b7280);
}
.req-form__fields {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.req-form__field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.req-form__field label {
  font-size: var(--cat-text-sm, 13px);
  font-weight: 500;
  color: var(--cat-muted, #6b7280);
}
.req-form__field select,
.req-form__field input[type="text"],
.req-form__field input[type="number"] {
  width: 100%;
  padding: 8px 12px;
  font-size: var(--cat-text-base, 14px);
  border: 1px solid var(--cat-border, #d1d5db);
  border-radius: var(--cat-radius-md, 6px);
  background: var(--cat-surface, #fff);
  color: var(--cat-text, #1f2937);
  outline: none;
}
.req-form__field select:focus,
.req-form__field input:focus {
  border-color: var(--cat-primary, #2563eb);
  box-shadow: 0 0 0 2px rgba(37, 99, 235, .1);
}
.req-form__field input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}
.req-form__actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}
.req-form__btn {
  padding: 10px 24px;
  font-size: var(--cat-text-base, 14px);
  border: 1px solid var(--cat-border, #d1d5db);
  border-radius: var(--cat-radius-md, 6px);
  background: var(--cat-surface, #fff);
  cursor: pointer;
  color: var(--cat-text, #1f2937);
}
.req-form__btn--primary {
  background: var(--cat-primary, #2563eb);
  color: #fff;
  border-color: var(--cat-primary, #2563eb);
}
.req-form__btn--primary:disabled {
  opacity: .6;
  cursor: default;
}
.req-form__btn:not(:disabled):hover {
  filter: brightness(.95);
}
.req-form__result {
  margin-top: 20px;
  padding: 12px;
  background: var(--cat-bg, #f9fafb);
  border-radius: var(--cat-radius-md, 6px);
  font-size: var(--cat-text-sm, 13px);
  color: var(--cat-muted, #6b7280);
}
.req-form__result code {
  font-family: var(--cat-font-mono, monospace);
  font-size: var(--cat-text-xs, 12px);
  color: var(--cat-primary, #2563eb);
}
</style>
