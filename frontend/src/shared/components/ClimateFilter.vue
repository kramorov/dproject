<!-- shared/components/ClimateFilter.vue -->
<!-- Каскадный фильтр климатического исполнения (ГОСТ 15150-69): зона → размещение → описание → t°. -->
<template>
  <div :class="compact ? 'exd-filter exd-filter--compact' : 'exd-filter'">
    <div class="filter-group-border">
    <!-- Text input for parsing climate string -->
    <div class="exd-parse-row" v-if="!compact">
      <input
        v-model="climateString"
        type="text"
        placeholder="...или введите климатическое исполнение"
        class="exd-parse-input"
        autocomplete="off"
        @keydown.enter.prevent
        @input="onParseInput"
      />
    </div>
    <div class="exd-parse-error" v-if="!compact && parseError">{{ parseError }}</div>

    <div class="exd-rows">
    <!-- Климатическая зона -->
    <div class="exd-row">
      <label v-if="!compact">Клим. зона</label>
      <select v-model="zoneId" @change="onZoneChange">
        <option :value="null">{{ compact ? 'Зона' : 'Не указано' }}</option>
        <option v-for="z in zones" :key="z.id" :value="z.id">{{ z.name }}</option>
      </select>
    </div>

    <!-- Категория размещения -->
    <div class="exd-row">
      <label v-if="!compact">Размещение</label>
      <select v-model="placementId" @change="onPlacementChange" class="exd-sel--narrow">
        <option :value="null">{{ compact ? 'Разм.' : 'Не указано' }}</option>
        <option v-for="p in availablePlacements" :key="p.id" :value="p.id">{{ p.code }}</option>
      </select>
    </div>
    </div>

    <!-- Расшифровка -->
    <div class="exd-row exd-description" v-if="!compact">
      <label>Описание</label>
      <div class="exd-description-text">{{ climateDescription || 'Не указано климатическое исполнение' }}</div>
    </div></div>

    <div v-if="loading" class="exd-loading">загрузка...</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/shared/api'

const props = defineProps({
  compact: { type: Boolean, default: false },
})

const emit = defineEmits(['update:temps'])

const zones = ref([])
const placements = ref([])
const conditions = ref([])
const zoneId = ref(null)
const placementId = ref(null)
const loading = ref(false)
const climateString = ref('')
const parseError = ref('')

let parseTimer = null

onMounted(async () => {
  try {
    const { data } = await api.get('/core/climate/structure/')
    zones.value = data.zones || []
    placements.value = data.placements || []
    conditions.value = data.conditions || []
  } catch (e) {
    console.error('[ClimateFilter] Failed to load structure', e)
  }
})

// Доступные размещения — все (показываем всегда, подсвечиваем невалидные комбинации при выборе)
const availablePlacements = computed(() => placements.value)

const selectedZone = computed(() =>
  zoneId.value ? zones.value.find(z => z.id === zoneId.value) : null
)

const selectedPlacement = computed(() =>
  placementId.value ? placements.value.find(p => p.id === placementId.value) : null
)

const matchedCondition = computed(() => {
  if (!zoneId.value || !placementId.value) return null
  return conditions.value.find(
    c => c.climaticPlacement_id === zoneId.value && c.climaticZone_id === placementId.value
  ) || null
})

const climateDescription = computed(() => {
  if (!zoneId.value) return null
  const parts = []
  if (selectedZone.value) {
    const zd = selectedZone.value.description ? ` (${selectedZone.value.description})` : ''
    parts.push(`${selectedZone.value.name}${zd}`)
  }
  if (selectedPlacement.value) {
    const pd = selectedPlacement.value.description ? ` (${selectedPlacement.value.description})` : ''
    parts.push(`категория размещения ${selectedPlacement.value.code}${pd}`)
  }
  if (matchedCondition.value) {
    parts.push(
      `Температура: от ${matchedCondition.value.min_temp_work}°C до ${matchedCondition.value.max_temp_work}°C`
    )
    if (matchedCondition.value.min_temp_extremal != null) {
      parts.push(
        `(предельная: от ${matchedCondition.value.min_temp_extremal}°C до ${matchedCondition.value.max_temp_extremal}°C)`
      )
    }
  } else if (zoneId.value && placementId.value) {
    parts.push('⚠ Комбинация не найдена в базе')
  }
  return parts.join(', ')
})

function emitTemps() {
  if (matchedCondition.value) {
    emit('update:temps', {
      zone_id: zoneId.value,
      placement_id: placementId.value,
      min_temp: matchedCondition.value.min_temp_work,
      max_temp: matchedCondition.value.max_temp_work,
      designation: `${selectedZone.value?.name || ''}${selectedPlacement.value?.code || ''}`,
    })
  } else {
    emit('update:temps', null)
  }
}

function onZoneChange() {
  emitTemps()
}

function onPlacementChange() {
  emitTemps()
}

async function onParseInput() {
  clearTimeout(parseTimer)
  parseError.value = ''
  const val = climateString.value.trim()
  if (!val) return

  parseTimer = setTimeout(async () => {
    try {
      const { data } = await api.post('/core/climate/parse/', { climate_string: val })
      if (data.error) {
        parseError.value = data.error
        return
      }
      if (data.zone_id != null) zoneId.value = data.zone_id
      if (data.placement_id != null) placementId.value = data.placement_id
      emitTemps()
    } catch (e) {
      const msg = e?.response?.data?.error || e?.message || 'Ошибка парсинга'
      parseError.value = msg
    }
  }, 400)
}
</script>

<style scoped>
/* Переиспользуем стили ExdFilter — классы exd-* уже определены в ExdFilter.vue */
/* При использовании вместе с ExdFilter стили не дублируются (scoped) */
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
