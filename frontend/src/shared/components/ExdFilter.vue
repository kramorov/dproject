<!-- shared/components/ExdFilter.vue -->
<!-- Каскадный фильтр взрывозащиты: метод → тип → группа → температура. -->
<template>
  <div class="exd-filter filter-group-border">
    <span class="exd-title">Взрывозащита</span>
    <!-- Text input for parsing -->
      <input
        v-model="exdString"
        type="text"
        placeholder="...или введите код взрывозащиты"
        class="exd-parse-input"
        autocomplete="off"
        @keydown.enter.prevent
        @input="onParseInput"
      />
      <div class="exd-parse-error" v-if="parseError">{{ parseError }}</div>

    <!-- Selects row -->
    <div class="exd-rows">
      <div class="exd-row">
        <label>Ex</label>
        <select v-model="methodId" @change="onMethodChange">
          <option :value="null">Все</option>
          <option :value="0">Общепром.</option>
          <option v-for="m in methods" :key="m.id" :value="m.id">Ex {{ m.code }}</option>
        </select>
      </div>
      <div class="exd-row">
        <label>Тип</label>
        <select v-model="typeId" @change="onTypeChange" class="exd-sel--narrow"
                :disabled="!methodId || String(methodId) === '0'">
          <option :value="null">Тип</option>
          <option v-for="t in availableTypes" :key="t.id" :value="t.id">{{ t.code }}</option>
        </select>
      </div>
      <div class="exd-row">
        <label>Группа</label>
        <select v-model="groupId" @change="onGroupChange" class="exd-sel--narrow"
                :disabled="!methodId || String(methodId) === '0'">
          <option :value="null">Группа</option>
          <optgroup v-if="!selectedTypeCategory || selectedTypeCategory === 'GAS'" label="Газ">
            <option v-for="g in gasGroups" :key="g.id" :value="g.id">{{ g.code }}</option>
          </optgroup>
          <optgroup v-if="!selectedTypeCategory || selectedTypeCategory === 'DUST'" label="Пыль">
            <option v-for="g in dustGroups" :key="g.id" :value="g.id">{{ g.code }}</option>
          </optgroup>
        </select>
      </div>
      <div class="exd-row">
        <label>T&deg;</label>
        <select v-model="tempId" @change="onTempChange" class="exd-sel--narrow"
                :disabled="!methodId || String(methodId) === '0' || isDustGroup">
          <option :value="null">T-класс</option>
          <option v-for="t in tempClasses" :key="t.id" :value="t.id">{{ t.code }}</option>
        </select>
      </div>
    </div>

    <!-- Description -->
    <div class="exd-row exd-description">
        <label>Описание</label>
      <div class="exd-description-text">{{ exdDescription || 'Не указан класс взрывозащиты' }}</div>
    </div>

    <div v-if="loading" class="exd-loading">загрузка...</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/shared/api'

const emit = defineEmits(['update:modelValue'])

const SENTINEL_NONE = '_none_'
const SENTINEL_EMPTY = '_empty_'

const methods = ref([])
const gasGroups = ref([])
const dustGroups = ref([])
const tempClasses = ref([])
const methodId = ref(null)
const typeId = ref(null)
const groupId = ref(null)
const tempId = ref(null)
const loading = ref(false)
const exdString = ref('')
const parseError = ref('')

let fetchTimer = null
let parseTimer = null

const availableTypes = computed(() => {
  if (!methodId.value) return []
  const m = methods.value.find(x => x.id === methodId.value)
  return m?.types || []
})

const isDustGroup = computed(() => {
  if (!groupId.value) return false
  return dustGroups.value.some(g => String(g.id) === String(groupId.value))
})

const selectedMethod = computed(() =>
  methodId.value ? methods.value.find(m => m.id === methodId.value) : null
)

const selectedType = computed(() => {
  if (!typeId.value) return null
  return availableTypes.value.find(t => t.id === typeId.value) || null
})

const selectedTypeCategory = computed(() => selectedType.value?.category || null)

const selectedGroup = computed(() => {
  if (!groupId.value) return null
  return [...gasGroups.value, ...dustGroups.value].find(g => String(g.id) === String(groupId.value)) || null
})

const selectedTempClass = computed(() => {
  if (!tempId.value) return null
  return tempClasses.value.find(t => String(t.id) === String(tempId.value)) || null
})

const exdDescription = computed(() => {
  if (methodId.value == null) return null
  if (String(methodId.value) === '0') return 'Взрывозащита — нет, Общепромышленное исполнение'

  const parts = []
  if (selectedType.value) {
    const tDesc = selectedType.value.description || selectedType.value.name || ''
    parts.push(`Ex ${selectedType.value.code}${tDesc ? ' (' + tDesc + ')' : ''}`)
  } else if (selectedMethod.value) {
    parts.push(selectedMethod.value.name || selectedMethod.value.code)
  }
  if (selectedGroup.value) {
    const gd = selectedGroup.value.description ? ` (${selectedGroup.value.description})` : ''
    parts.push(`группа опасности среды ${selectedGroup.value.code}${gd}`)
  }
  if (selectedTempClass.value) {
    const td = selectedTempClass.value.description ? ` (${selectedTempClass.value.description})` : ''
    parts.push(`${selectedTempClass.value.code}${td}, до ${selectedTempClass.value.max_temp}°C`)
  }
  return parts.join(', ')
})

onMounted(async () => {
  try {
    const { data } = await api.get('/core/exd/structure/')
    methods.value = data.methods || []
    gasGroups.value = data.gas_groups || data.groups?.filter(g => g.group_type === 'GAS') || []
    dustGroups.value = data.dust_groups || data.groups?.filter(g => g.group_type === 'DUST') || []
    tempClasses.value = data.temperature_classes || []
  } catch (e) {
    console.error('[ExdFilter] Failed to load structure', e)
  }
})

async function fetchCompatible() {
  if (String(methodId.value) === '0') {
    emit('update:modelValue', [SENTINEL_NONE])
    return
  }
  if (methodId.value == null) {
    emit('update:modelValue', [])
    return
  }

  const params = {}
  params.method_id = methodId.value
  if (typeId.value) params.type_id = typeId.value
  if (groupId.value) params.group_id = groupId.value
  if (tempId.value && !isDustGroup.value) params.temp_id = tempId.value

  loading.value = true
  try {
    const { data } = await api.get('/core/exd/compatible/', { params })
    const ids = data.ids || []
    emit('update:modelValue', ids.length === 0 ? [SENTINEL_EMPTY] : ids)
  } catch (e) {
    console.error('[ExdFilter] Compatible fetch failed', e)
    emit('update:modelValue', [SENTINEL_EMPTY])
  }
  loading.value = false
}

function debouncedFetch() {
  clearTimeout(fetchTimer)
  fetchTimer = setTimeout(fetchCompatible, 200)
}

function onMethodChange() { typeId.value = null; groupId.value = null; tempId.value = null; debouncedFetch() }
function onTypeChange() { debouncedFetch() }
function onGroupChange() { tempId.value = null; debouncedFetch() }
function onTempChange() { debouncedFetch() }

async function onParseInput() {
  clearTimeout(parseTimer)
  parseError.value = ''
  const val = exdString.value.trim()
  if (!val) return

  parseTimer = setTimeout(async () => {
    try {
      const { data } = await api.post('/core/exd/parse/', { exd_string: val })
      if (!data.method_id && !data.type_id && !data.group_id && !data.temp_id) {
        methodId.value = null; typeId.value = null; groupId.value = null; tempId.value = null
        debouncedFetch()
        return
      }
      if (data.error) { parseError.value = data.error; return }
      if (data.method_id != null) methodId.value = data.method_id
      if (data.type_id != null) typeId.value = data.type_id
      if (data.group_id != null) groupId.value = data.group_id
      if (data.temp_id != null) tempId.value = data.temp_id
      debouncedFetch()
    } catch (e) {
      parseError.value = e?.response?.data?.error || e?.message || 'Ошибка парсинга'
    }
  }, 400)
}
</script>

<style scoped>
.exd-filter { display: flex; flex-direction: column; gap: 6px; position: relative; }
.exd-title {
  position: absolute; top: -8px; left: 10px;
  font-size: 11px; font-weight: 500; color: var(--cat-muted, #9ca3af);
  background: var(--cat-surface, #fff); padding: 0 4px;
}
.exd-rows { display: flex; flex-direction: row; flex-wrap: wrap; gap: 6px; align-items: flex-end; }
.exd-row { display: flex; flex-direction: column; gap: 1px; }
.exd-row label { font-size: 11px; font-weight: 500; color: var(--cat-muted, #9ca3af); }
.exd-row select { padding: 4px 6px; font-size: 12px; color: var(--cat-text, #1f2937); border: 1px solid var(--cat-border, #d1d5db); border-radius: 4px; background: var(--cat-surface, #fff); width: auto; min-width: 80px; }
.exd-sel--narrow { min-width: 55px !important; }
.exd-row select:disabled { opacity: .4; cursor: default; }

.exd-parse-input { width: 100%; padding: 4px 6px; font-size: 12px; font-family: var(--cat-font-mono, monospace); border: 1px solid var(--cat-border, #d1d5db); border-radius: 4px; background: var(--cat-surface, #fff); color: var(--cat-text, #1f2937); outline: none; }
.exd-parse-input:focus { border-color: var(--cat-primary, #2563eb); }
.exd-parse-input::placeholder { color: var(--cat-muted-light, #cbd5e1); }
.exd-parse-error { font-size: 10px; color: #dc2626; margin-top: 2px; }

.exd-loading { font-size: 11px; color: var(--cat-muted, #6b7280); text-align: center; }

.exd-description-text {
  font-size: 12px; color: var(--cat-text, #1f2937);
  background: var(--cat-bg, #f3f4f6); padding: 6px 8px;
  border-radius: 4px; line-height: 1.4;
  max-height: 80px; overflow-y: auto;
}
</style>
