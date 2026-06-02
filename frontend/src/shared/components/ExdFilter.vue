<!-- shared/components/ExdFilter.vue -->
<!-- Каскадный фильтр взрывозащиты: метод → тип → группа → температура. -->
<template>
  <div class="exd-filter">
    <!-- Метод -->
    <div class="exd-row">
      <label>Метод</label>
      <select v-model="methodId" @change="onMethodChange">
        <option :value="null">Все</option>
        <option :value="0">Общепромышленное (без Ex)</option>
        <option v-for="m in methods" :key="m.id" :value="m.id">{{ m.name }}</option>
      </select>
    </div>

    <!-- Тип (только для Ex-методов, не для общепромышленного) -->
    <div class="exd-row" v-if="methodId && methodId !== 0">
      <label>Тип</label>
      <select v-model="typeId" @change="onTypeChange">
        <option :value="null">Все типы</option>
        <option v-for="t in availableTypes" :key="t.id" :value="t.id">{{ t.code }} — {{ t.name }}</option>
      </select>
    </div>

    <!-- Группа (только для Ex-методов) -->
    <div class="exd-row" v-if="methodId && methodId !== 0">
      <label>Группа среды</label>
      <select v-model="groupId" @change="onGroupChange">
        <option :value="null">Все группы</option>
        <optgroup label="Газ">
          <option v-for="g in gasGroups" :key="g.id" :value="g.id">{{ g.code }}</option>
        </optgroup>
        <optgroup label="Пыль">
          <option v-for="g in dustGroups" :key="g.id" :value="g.id">{{ g.code }}</option>
        </optgroup>
      </select>
    </div>

    <!-- Температура (только для газа, не для общепромышленного) -->
    <div class="exd-row" v-if="methodId && methodId !== 0 && !isDustGroup">
      <label>Темп. класс</label>
      <select v-model="tempId" @change="onTempChange">
        <option :value="null">Все классы</option>
        <option v-for="t in tempClasses" :key="t.id" :value="t.id">{{ t.code }} ({{ t.max_temp }}°C)</option>
      </select>
    </div>
    <div class="exd-row exd-dust-note" v-if="methodId && methodId !== 0 && isDustGroup">
      <span class="exd-hint">Температурный класс — настраивается в свойствах ExdOption</span>
    </div>

    <div v-if="loading" class="exd-loading">загрузка...</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/shared/api'

const emit = defineEmits(['update:modelValue'])

const SENTINEL_NONE = '_none_'   // общепромышленное — exd отсутствует
const SENTINEL_EMPTY = '_empty_' // Ex-метод без совместимых — ничего не найдено

const methods = ref([])
const gasGroups = ref([])
const dustGroups = ref([])
const tempClasses = ref([])
const methodId = ref(null)       // null=все, 0=общепром, >0=Ex-метод
const typeId = ref(null)
const groupId = ref(null)
const tempId = ref(null)
const loading = ref(false)

let fetchTimer = null

const availableTypes = computed(() => {
  if (!methodId.value) return []
  const m = methods.value.find(x => x.id === methodId.value)
  return m?.types || []
})

const isDustGroup = computed(() => {
  if (!groupId.value) return false
  return dustGroups.value.some(g => g.id === groupId.value)
})

// Fetch structure
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

// Fetch compatible IDs
async function fetchCompatible() {
  // ── Общепромышленное (без Ex) ──
  if (methodId.value === 0) {
    emit('update:modelValue', [SENTINEL_NONE])
    return
  }

  // ── Ничего не выбрано ──
  if (!methodId.value) {
    emit('update:modelValue', [])
    return
  }

  // ── Ex-метод выбран — запрос совместимых ID ──
  const params = {}
  params.method_id = methodId.value
  if (typeId.value) params.type_id = typeId.value
  if (groupId.value) params.group_id = groupId.value
  if (tempId.value && !isDustGroup.value) params.temp_id = tempId.value

  loading.value = true
  try {
    const { data } = await api.get('/core/exd/compatible/', { params })
    const ids = data.ids || []
    if (ids.length === 0) {
      // Метод выбран, но совместимых ExdOption нет → ничего не найдено
      emit('update:modelValue', [SENTINEL_EMPTY])
    } else {
      emit('update:modelValue', ids)
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

function onMethodChange() {
  typeId.value = null
  groupId.value = null
  tempId.value = null
  debouncedFetch()
}
function onTypeChange() { debouncedFetch() }
function onGroupChange() {
  tempId.value = null
  debouncedFetch()
}
function onTempChange() { debouncedFetch() }
</script>

<style scoped>
.exd-filter { display: flex; flex-direction: column; gap: 8px; }
.exd-row { display: flex; flex-direction: column; gap: 2px; }
.exd-row label { font-size: var(--cat-text-sm); font-weight: 500; color: var(--cat-muted); }
.exd-row select { width: 100%; padding: 6px 8px; font-size: var(--cat-text-base); color: var(--cat-text); border: 1px solid var(--cat-border); border-radius: var(--cat-radius-md); background: var(--cat-surface); }
.exd-loading { font-size: 12px; color: var(--cat-muted); text-align: center; padding: 4px; }
.exd-dust-note { padding: 4px 0; }
.exd-hint { font-size: 12px; color: var(--cat-muted-light); font-style: italic; }
</style>
