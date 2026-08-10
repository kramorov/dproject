<!-- shared/components/ClimateFilter.vue -->
<!-- Каскадный фильтр климатического исполнения (ГОСТ 15150-69). -->
<template>
  <div class="exd-filter filter-group-border">
    <span class="climate-title">Температура</span>
    <!-- Text input -->
      <input
        v-model="climateString"
        type="text"
        placeholder="...или введите климатическое исполнение"
        class="exd-parse-input"
        autocomplete="off"
        @keydown.enter.prevent
        @input="onParseInput"
      />
      <div class="exd-parse-error" v-if="parseError">{{ parseError }}</div>

    <!-- Row: zone + placement + temp inputs -->
    <div class="climate-rows">
      <div class="exd-row">
        <label>Зона</label>
        <select v-model="zoneId" @change="onZoneChange">
          <option :value="null">—</option>
          <option v-for="z in zones" :key="z.id" :value="z.id">{{ z.name }}</option>
        </select>
      </div>
      <div class="exd-row">
        <label>Разм.</label>
        <select v-model="placementId" @change="onPlacementChange" class="exd-sel--narrow">
          <option :value="null">—</option>
          <option v-for="p in availablePlacements" :key="p.id" :value="p.id">{{ p.code }}</option>
        </select>
      </div>
      <div class="exd-row">
        <label>t мин</label>
        <input v-model="manualMinTemp" type="number" class="climate-temp-input"
               :readonly="tempsLocked" :class="{ 'climate-temp-input--locked': tempsLocked }" />
      </div>
      <div class="exd-row">
        <label>t макс</label>
        <input v-model="manualMaxTemp" type="number" class="climate-temp-input"
               :readonly="tempsLocked" :class="{ 'climate-temp-input--locked': tempsLocked }" />
      </div>
    </div>

    <!-- Description -->
    <div class="exd-row exd-description">
        <label>Описание</label>
        <div class="exd-description-text">{{ climateDescription || 'Не указано климатическое исполнение' }}</div>
    </div>

    <div v-if="loading" class="exd-loading">загрузка...</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import api from '@/shared/api'

const emit = defineEmits(['update:temps'])

const zones = ref([])
const placements = ref([])
const conditions = ref([])
const zoneId = ref(null)
const placementId = ref(null)
const loading = ref(false)
const climateString = ref('')
const parseError = ref('')
const manualMinTemp = ref(null)
const manualMaxTemp = ref(null)
let parseTimer = null
let tempEmitTimer = null

onMounted(async () => {
  try {
    const { data } = await api.get('/core/climate/structure/')
    zones.value = data.zones || []
    placements.value = data.placements || []
    conditions.value = data.conditions || []
  } catch (e) { console.error('[ClimateFilter] Failed to load structure', e) }
})

const availablePlacements = computed(() => placements.value)
const selectedZone = computed(() => zoneId.value ? zones.value.find(z => z.id === zoneId.value) : null)
const selectedPlacement = computed(() => placementId.value ? placements.value.find(p => p.id === placementId.value) : null)

const matchedCondition = computed(() => {
  if (!zoneId.value || !placementId.value) return null
  return conditions.value.find(c => c.climaticZone_id === zoneId.value && c.climaticPlacement_id === placementId.value) || null
})

const tempsLocked = computed(() => !!(matchedCondition.value || climateString.value.trim()))

watch([matchedCondition, () => climateString.value.trim()], () => {
  if (matchedCondition.value) {
    manualMinTemp.value = matchedCondition.value.min_temp_work
    manualMaxTemp.value = matchedCondition.value.max_temp_work
  }
}, { immediate: true })

const climateDescription = computed(() => {
  if (!zoneId.value && manualMinTemp.value == null && manualMaxTemp.value == null) return null
  const parts = []
  if (selectedZone.value) {
    parts.push(selectedZone.value.name + (selectedZone.value.description ? ` (${selectedZone.value.description})` : ''))
  }
  if (selectedPlacement.value) {
    parts.push(`кат. ${selectedPlacement.value.code}` + (selectedPlacement.value.description ? ` (${selectedPlacement.value.description})` : ''))
  }
  if (matchedCondition.value) {
    parts.push(`t: ${matchedCondition.value.min_temp_work}…${matchedCondition.value.max_temp_work}°C`)
    if (matchedCondition.value.min_temp_extremal != null) {
      parts.push(`(пред.: ${matchedCondition.value.min_temp_extremal}…${matchedCondition.value.max_temp_extremal}°C)`)
    }
  } else if (manualMinTemp.value != null || manualMaxTemp.value != null) {
    parts.push(`t (вручную): ${manualMinTemp.value ?? '…'}…${manualMaxTemp.value ?? '…'}°C`)
  } else if (zoneId.value && placementId.value) {
    parts.push('⚠ Комбинация не найдена')
  }
  return parts.join(', ')
})

function emitTemps() {
  if (matchedCondition.value) {
    emit('update:temps', { zone_id: zoneId.value, placement_id: placementId.value,
      min_temp: matchedCondition.value.min_temp_work, max_temp: matchedCondition.value.max_temp_work,
      designation: `${selectedZone.value?.name || ''}${selectedPlacement.value?.code || ''}` })
  } else if (manualMinTemp.value != null || manualMaxTemp.value != null) {
    const temps = { zone_id: zoneId.value, placement_id: placementId.value, designation: 'вручную' }
    if (manualMinTemp.value != null) temps.min_temp = Number(manualMinTemp.value)
    if (manualMaxTemp.value != null) temps.max_temp = Number(manualMaxTemp.value)
    emit('update:temps', temps)
  } else { emit('update:temps', null) }
}

async function onZoneChange() {
  await nextTick()
  if (matchedCondition.value) {
    manualMinTemp.value = matchedCondition.value.min_temp_work
    manualMaxTemp.value = matchedCondition.value.max_temp_work
  } else if (!placementId.value) {
    // placement not yet selected — keep current temps, don't reset
  } else {
    manualMinTemp.value = null
    manualMaxTemp.value = null
  }
  emitTemps()
}
async function onPlacementChange() {
  await nextTick()
  if (matchedCondition.value) {
    manualMinTemp.value = matchedCondition.value.min_temp_work
    manualMaxTemp.value = matchedCondition.value.max_temp_work
  } else {
    manualMinTemp.value = null
    manualMaxTemp.value = null
  }
  emitTemps()
}
watch([manualMinTemp, manualMaxTemp], () => {
  if (tempsLocked.value) return
  clearTimeout(tempEmitTimer)
  tempEmitTimer = setTimeout(() => emitTemps(), 400)
})
watch(matchedCondition, (mc) => {
  if (mc) {
    manualMinTemp.value = mc.min_temp_work
    manualMaxTemp.value = mc.max_temp_work
    emitTemps()
  }
})

async function onParseInput() {
  clearTimeout(parseTimer); parseError.value = ''
  const val = climateString.value.trim()
  if (!val) return
  parseTimer = setTimeout(async () => {
    try {
      const { data } = await api.post('/core/climate/parse/', { climate_string: val })
      if (data.error) { parseError.value = data.error; return }
      if (data.zone_id != null) zoneId.value = data.zone_id
      if (data.placement_id != null) placementId.value = data.placement_id
      emitTemps()
    } catch (e) { parseError.value = e?.response?.data?.error || e?.message || 'Ошибка парсинга' }
  }, 400)
}
</script>

<style scoped>
.exd-filter { display: flex; flex-direction: column; gap: 6px; position: relative; }
.climate-title {
  position: absolute; top: -8px; left: 10px;
  font-size: 11px; font-weight: 500; color: var(--cat-muted, #9ca3af);
  background: var(--cat-surface, #fff); padding: 0 4px;
}
.climate-rows { display: flex; flex-direction: row; flex-wrap: wrap; gap: 6px; align-items: flex-end; justify-content: space-between; }
.exd-row { display: flex; flex-direction: column; gap: 1px; }
.exd-row label { font-size: 11px; font-weight: 500; color: var(--cat-muted, #9ca3af); }
.climate-rows .exd-row { flex: 1; }
.climate-rows .exd-row select { width: 100%; padding: 4px 6px; font-size: 12px; color: var(--cat-text, #1f2937); border: 1px solid var(--cat-border, #d1d5db); border-radius: 4px; background: var(--cat-surface, #fff); }
.climate-rows .exd-sel--narrow { min-width: 0; }

.climate-temp-input { width: 100%; box-sizing: border-box; padding: 4px 2px; font-size: 12px; text-align: center; border: 1px solid var(--cat-border, #d1d5db); border-radius: 4px; background: var(--cat-surface, #fff); color: var(--cat-text, #1f2937); outline: none; -moz-appearance: textfield; }
.climate-temp-input::-webkit-outer-spin-button, .climate-temp-input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
.climate-temp-input:focus { border-color: var(--cat-primary, #2563eb); }
.climate-temp-input--locked { background: var(--cat-bg, #f3f4f6); color: var(--cat-muted, #6b7280); cursor: default; }

.exd-parse-input { width: 100%; padding: 4px 6px; font-size: 12px; font-family: var(--cat-font-mono, monospace); border: 1px solid var(--cat-border, #d1d5db); border-radius: 4px; background: var(--cat-surface, #fff); color: var(--cat-text, #1f2937); outline: none; }
.exd-parse-input:focus { border-color: var(--cat-primary, #2563eb); }
.exd-parse-input::placeholder { color: var(--cat-muted-light, #cbd5e1); }
.exd-parse-error { font-size: 10px; color: #dc2626; margin-top: 2px; }

.exd-loading { font-size: 11px; color: var(--cat-muted, #6b7280); text-align: center; }

.exd-description-text { font-size: 12px; color: var(--cat-text, #1f2937); background: var(--cat-bg, #f3f4f6); padding: 6px 8px; border-radius: 4px; line-height: 1.4; max-height: 80px; overflow-y: auto; }
</style>
