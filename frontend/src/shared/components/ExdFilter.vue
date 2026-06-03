<!-- shared/components/ExdFilter.vue -->
<!-- Каскадный фильтр взрывозащиты: метод → тип → группа → температура. -->
<template>
  <div :class="compact ? 'exd-filter exd-filter--compact' : 'exd-filter'">
    <div class="filter-group-border">
    <!-- Text input for parsing Exd string -->
    <div class="exd-parse-row" v-if="!compact">
      <input
        v-model="exdString"
        type="text"
        placeholder="...или введите код взрывозащиты"
        class="exd-parse-input"
        autocomplete="off"
        @keydown.enter.prevent
        @input="onParseInput"
      />
    </div>
    <div class="exd-parse-error" v-if="!compact && parseError">{{ parseError }}</div>

    <div class="exd-rows">
    <!-- Метод -->
    <div class="exd-row">
      <label v-if="!compact">Метод Ex</label>
      <select v-model="methodId" @change="onMethodChange">
        <option :value="null">Все</option>
        <option :value="0">{{ compact ? 'Общепром.' : 'Общепромышленное (без Ex)' }}</option>
        <option v-for="m in methods" :key="m.id" :value="m.id">Ex {{ m.code }}</option>
      </select>
    </div>

    <!-- Тип (только для Ex-методов, не для общепромышленного) -->
    <div class="exd-row" v-if="methodId && String(methodId) !== '0'">
      <label v-if="!compact">Тип</label>
      <select v-model="typeId" @change="onTypeChange" class="exd-sel--narrow">
        <option :value="null">{{ compact ? 'Тип' : 'Все типы' }}</option>
        <option v-for="t in availableTypes" :key="t.id" :value="t.id">{{ t.code }}</option>
      </select>
    </div>

    <!-- Группа (только для Ex-методов) -->
    <div class="exd-row" v-if="methodId && String(methodId) !== '0'">
      <label v-if="!compact">Группа среды</label>
      <select v-model="groupId" @change="onGroupChange" class="exd-sel--narrow">
        <option :value="null">{{ compact ? 'Группа' : 'Все группы' }}</option>
        <optgroup v-if="!selectedTypeCategory || selectedTypeCategory === 'GAS'" label="Газ">
          <option v-for="g in gasGroups" :key="g.id" :value="g.id">{{ g.code }}</option>
        </optgroup>
        <optgroup v-if="!selectedTypeCategory || selectedTypeCategory === 'DUST'" label="Пыль">
          <option v-for="g in dustGroups" :key="g.id" :value="g.id">{{ g.code }}</option>
        </optgroup>
      </select>
    </div>

    <!-- Температура (только для газа, не для общепромышленного) -->
    <div class="exd-row" v-if="methodId && String(methodId) !== '0' && !isDustGroup">
      <label v-if="!compact">Темп. класс</label>
      <select v-model="tempId" @change="onTempChange" class="exd-sel--narrow">
        <option :value="null">{{ compact ? 'T-класс' : 'Все классы' }}</option>
        <option v-for="t in tempClasses" :key="t.id" :value="t.id">{{ t.code }}</option>
      </select>
    </div>
    <div class="exd-row exd-dust-note" v-if="!compact && methodId && String(methodId) !== '0' && isDustGroup">
      <span class="exd-hint">Температурный класс — настраивается в свойствах ExdOption</span>
    </div>

    </div>

    <!-- Расшифровка -->
    <div class="exd-row exd-description" v-if="!compact">
      <label>Описание</label>
      <div class="exd-description-text">{{ exdDescription || 'Не указан класс взрывозащиты' }}</div>
    </div></div>

    <div v-if="loading" class="exd-loading">загрузка...</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/shared/api'

const props = defineProps({
  compact: { type: Boolean, default: false },
  single: { type: Boolean, default: false },
})

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
  // «Все» — ничего не выбрано
  if (methodId.value == null) return null
  // «Общепромышленное»
  if (String(methodId.value) === '0') return 'Взрывозащита — нет, Общепромышленное исполнение'

  const parts = []
  // Метод или Тип: если выбран тип — показываем его вместо метода
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
    emit('update:modelValue', props.single ? SENTINEL_NONE : [SENTINEL_NONE])
    return
  }
  if (methodId.value == null) {
    emit('update:modelValue', props.single ? null : [])
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
    if (props.single) {
      emit('update:modelValue', ids.length === 0 ? SENTINEL_EMPTY : (ids[0] || null))
    } else {
      emit('update:modelValue', ids.length === 0 ? [SENTINEL_EMPTY] : ids)
    }
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
      console.log('[ExdFilter] parse result:', data)
      // Empty result → reset cascade
      if (!data.method_id && !data.type_id && !data.group_id && !data.temp_id) {
        methodId.value = null; typeId.value = null; groupId.value = null; tempId.value = null
        debouncedFetch()
        return
      }
      if (data.error) {
        parseError.value = data.error
        return
      }
      // Fill cascade selects
      if (data.method_id != null) methodId.value = data.method_id
      if (data.type_id != null) typeId.value = data.type_id
      if (data.group_id != null) groupId.value = data.group_id
      if (data.temp_id != null) tempId.value = data.temp_id
      // Trigger single compatible fetch
      debouncedFetch()
    } catch (e) {
      const msg = e?.response?.data?.error || e?.message || 'Ошибка парсинга'
      parseError.value = msg
    }
  }, 400)
}
</script>

<style scoped>
.exd-filter { display: flex; flex-direction: column; gap: 8px; }
.exd-filter--compact { flex-direction: row; flex-wrap: wrap; gap: 6px; align-items: flex-end; }
.exd-filter:not(.exd-filter--compact) .exd-rows { display: flex; flex-direction: row; flex-wrap: wrap; gap: 8px; align-items: flex-end; }
.exd-row { display: flex; flex-direction: column; gap: 2px; }
.exd-filter--compact .exd-row { flex-direction: row; align-items: center; gap: 4px; }
.exd-filter:not(.exd-filter--compact) .exd-row select { width: auto; min-width: 100px; max-width: 160px; }
.exd-filter:not(.exd-filter--compact) .exd-row select.exd-sel--narrow { min-width: 70px; max-width: 110px; }

.exd-row label { font-size: var(--cat-text-sm); font-weight: 500; color: var(--cat-muted); }
.exd-row select { padding: 6px 8px; font-size: var(--cat-text-base); color: var(--cat-text); border: 1px solid var(--cat-border); border-radius: var(--cat-radius-md); background: var(--cat-surface); }
.exd-filter--compact .exd-row select { width: auto; padding: 6px 10px; font-size: var(--cat-text-sm, 13px); }

/* ── Parse input ── */
.exd-parse-row { margin-bottom: 6px; }
.exd-parse-input {
  width: 100%;
  padding: 5px 8px;
  font-size: var(--cat-text-sm, 13px);
  font-family: var(--cat-font-mono, monospace);
  border: 1px solid var(--cat-border, #d1d5db);
  border-radius: var(--cat-radius-sm, 4px);
  background: var(--cat-surface, #fff);
  color: var(--cat-text, #1f2937);
  outline: none;
}
.exd-parse-input:focus { border-color: var(--cat-primary, #2563eb); }
.exd-parse-input::placeholder { color: var(--cat-muted-light, #cbd5e1); font-family: var(--cat-font-mono, monospace); }
.exd-parse-error {
  font-size: 11px;
  color: #dc2626;
  margin-bottom: 6px;
}

.exd-loading { font-size: 12px; color: var(--cat-muted); text-align: center; padding: 4px; }
.exd-dust-note { padding: 4px 0; }
.exd-hint { font-size: 12px; color: var(--cat-muted-light); font-style: italic; }

/* ── Description ── */
.exd-description { margin-top: 2px; }
.exd-description-text {
  min-height: 42px;
  font-size: var(--cat-text-sm, 13px);
  color: var(--cat-text, #1f2937);
  background: var(--cat-bg, #f3f4f6);
  padding: 8px 10px;
  border-radius: var(--cat-radius-md, 6px);
  line-height: 1.4;
}
</style>