<!-- shared/components/catalog/EngineerFilterBar.vue -->
<!-- Horizontal filter bar for EngineerSelection. Row 1: regular selects, Row 2: Exd + Climate. -->
<template>
  <div class="eng-filter-bar">
    <!-- Header row: title + actions -->
    <div class="eng-filter-bar__header">
      <span class="eng-filter-bar__title">{{ t('catalog.engineer.filters') }}</span>
      <div class="eng-filter-bar__actions">
        <label class="eng-filter-bar__compat" v-if="showCompatibleToggle">
          <input type="checkbox" :checked="showCompatible" @change="$emit('toggleCompatible', $event.target.checked)" />
          {{ t('catalog.engineer.compatible') }}
        </label>
        <button class="eng-filter-bar__reset" @click="$emit('reset')" v-if="hasActive">{{ t('catalog.engineer.reset') }}</button>
      </div>
    </div>

    <!-- Row 1: regular filter selects (ungrouped) -->
    <div class="eng-filter-bar__chips" v-if="plainRegularFilters.length">
      <!-- Thread combined filter (type + size) -->
      <div v-if="hasThreadPair" class="eng-filter-bar__chip eng-filter-bar__thread">
        <ThreadFilter @change="onThreadChange" />
      </div>
      <div v-for="f in plainRegularFilters" :key="f.key" class="eng-filter-bar__chip" v-show="(!isThreadFilter(f.key) || !hasThreadPair) && isVisible(f.key)">
        <label class="eng-filter-bar__chip-label">{{ f.label }}</label>
        <input
          v-if="isNumericFilter(f)"
          type="number"
          class="eng-filter-bar__chip-input"
          min="0"
          step="0.1"
          v-model="active[f.key]"
          @change="$emit('change', f.key, active[f.key])"
        />
        <span v-else-if="f.options.length === 1" class="eng-filter-bar__chip-single">{{ f.options[0].name }}</span>
        <select
          v-else
          class="eng-filter-bar__chip-select"
          v-model="active[f.key]"
          @change="$emit('change', f.key, active[f.key])"
        >
          <option value="">{{ t('catalog.engineer.notSpecified') }}</option>
          <option v-for="opt in f.options" :key="opt.id" :value="opt.id">{{ f.show_code && opt.code ? opt.code + ' ' + opt.name : opt.name }}</option>
        </select>
      </div>
    </div>

    <!-- Grouped filter blocks (e.g. diameters) -->
    <div v-for="grp in groupedRegularFilters" :key="grp.label" class="eng-filter-bar__group">
      <span class="eng-filter-bar__group-label">{{ grp.label }}</span>
      <div class="eng-filter-bar__chips">
        <div v-for="f in grp.filters" :key="f.key" class="eng-filter-bar__chip" v-show="isVisible(f.key)">
          <label class="eng-filter-bar__chip-label">{{ f.label }}</label>
          <input
            v-if="isNumericFilter(f)"
            type="number"
            class="eng-filter-bar__chip-input"
            min="0"
            step="0.1"
            v-model="active[f.key]"
            @change="$emit('change', f.key, active[f.key])"
          />
          <span v-else-if="f.options.length === 1" class="eng-filter-bar__chip-single">{{ f.options[0].name }}</span>
          <select
            v-else
            class="eng-filter-bar__chip-select"
            v-model="active[f.key]"
            @change="$emit('change', f.key, active[f.key])"
          >
            <option value="">{{ t('catalog.engineer.notSpecified') }}</option>
            <option v-for="opt in f.options" :key="opt.id" :value="opt.id">{{ f.show_code && opt.code ? opt.code + ' ' + opt.name : opt.name }}</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Row 2: Exd + Climate (special cascade filters) -->
    <div class="eng-filter-bar__special" v-if="specialFilters.length">
      <div v-for="f in specialFilters" :key="f.key" class="eng-filter-bar__special-item">
        <ExdFilter
          v-if="f.filter_type === 'exd_compatible'"
          @update:modelValue="ids => onExdChange(ids)"
          @update:exactId="id => onExdExact(id)"
        />
        <ClimateFilter
          v-else-if="f.filter_type === 'climate_cascade'"
          @update:temps="temps => onClimateChange(temps, f.key)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, watch } from 'vue'
import ExdFilter from '@/shared/components/ExdFilter.vue'
import ClimateFilter from '@/shared/components/ClimateFilter.vue'
import ThreadFilter from '@/shared/components/ThreadFilter.vue'
import { useI18n } from '@/shared/i18n'
const { t } = useI18n()

const activeExdIds = ref([])

const props = defineProps({
  filters: { type: Object, default: () => ({}) },
  showCompatible: { type: Boolean, default: false },
  showCompatibleToggle: { type: Boolean, default: false },
})

const emit = defineEmits(['change', 'reset', 'toggleCompatible'])

const active = reactive({})

watch(() => props.filters, (val) => {
  for (const [k, v] of Object.entries(val)) {
    // Preserve existing selection, apply default_value only on first load
    if (active[k] === undefined || active[k] === '' || active[k] === null) {
      active[k] = v.default_value || ''
    } else {
      // Keep existing value (may be filter object from previous state)
      // active[k] already has correct value
    }
  }
}, { deep: true, immediate: true })

const allFilters = computed(() => {
  const arr = []
  for (const [key, val] of Object.entries(props.filters)) {
    if (val) arr.push({ key, ...val })
  }
  arr.sort((a, b) => (a.order || 99) - (b.order || 99))
  return arr
})

const hasClimateFilter = computed(() =>
  allFilters.value.some(f => f.filter_type === 'climate_cascade')
)

const regularFilters = computed(() =>
  allFilters.value.filter(f =>
    f.filter_type !== 'exd_compatible' && f.filter_type !== 'climate_cascade'
    && !(hasClimateFilter.value && (f.filter_type === 'temp_min' || f.filter_type === 'temp_max'))
  )
)

const plainRegularFilters = computed(() =>
  regularFilters.value.filter(f => !f.group)
)

const groupedRegularFilters = computed(() => {
  const groups = []
  const byLabel = {}
  for (const f of regularFilters.value) {
    if (!f.group) continue
    if (!byLabel[f.group]) {
      const grp = { label: f.group, filters: [] }
      byLabel[f.group] = grp
      groups.push(grp)
    }
    byLabel[f.group].filters.push(f)
  }
  return groups
})

const specialFilters = computed(() =>
  allFilters.value.filter(f =>
    f.filter_type === 'exd_compatible' || f.filter_type === 'climate_cascade'
  )
)

const hasActive = computed(() =>
  Object.values(active).some(v => v !== '' && v != null)
)

function onExdChange(ids) {
  activeExdIds.value = ids
  if (!ids.length) {
    emit('change', 'exd_id', '')
  } else if (ids[0] === '_none_' || ids[0] === '_empty_') {
    emit('change', 'exd_id', ids[0])
  } else {
    emit('change', 'exd_id', ids.join(','))
  }
}

function onExdExact(id) {
  emit('change', 'exd_id_exact', id != null ? id : '')
}

const THREAD_KEYS = ['thread_type_id', 'thread_id']
const NUMERIC_FILTER_TYPES = ['gte', 'lte']
function isNumericFilter(f) { return NUMERIC_FILTER_TYPES.includes(f.filter_type) }
const hasThreadPair = computed(() => THREAD_KEYS.every(k => k in props.filters))
function isThreadFilter(key) { return THREAD_KEYS.includes(key) }
function onThreadChange(v) { if (v.thread_type_id != null) emit('change', 'thread_type_id', v.thread_type_id); if (v.thread_id != null) emit('change', 'thread_id', v.thread_id) }

function onClimateChange(temps, key) {
  if (temps) {
    if (temps.min_temp != null) emit('change', 'work_temp_min', temps.min_temp)
    if (temps.max_temp != null) emit('change', 'work_temp_max', temps.max_temp)
  }
}
import api from '@/shared/api'

const visibleParams = ref(null)
function isVisible(key) {
  // Graph-wizard visibility (only active when graphCode is provided)
  if (visibleParams.value !== null) {
    if (THREAD_KEYS.includes(key)) {
      if (!(hasThreadPair.value && visibleParams.value.has(key))) return false
    } else if (!visibleParams.value.has(key)) {
      return false
    }
  }
  // Conditional visibility: visible_when maps a parent param to allowed option codes
  const f = props.filters[key]
  if (f && f.visible_when) {
    for (const [parentKey, codes] of Object.entries(f.visible_when)) {
      const parent = props.filters[parentKey]
      if (!parent) continue // родитель не в этом наборе фильтров — условие не применимо
      const selected = active[parentKey]
      if (selected === '' || selected == null) return false
      const opt = (parent.options || []).find(o => String(o.id) === String(selected))
      if (!opt || !codes.includes(opt.code)) return false
    }
  }
  return true
}

// Clear filters that became hidden by visible_when (UI); activeFilters чистится в useCatalog.fetchData()
watch(() => ({ ...active }), () => {
  for (const key of Object.keys(active)) {
    const f = props.filters[key]
    if (!f || !f.visible_when) continue
    if (active[key] && !isVisible(key)) {
      active[key] = ''
    }
  }
}, { deep: true })

watch(() => ({ ...active }), async () => {
  if (!props.graphCode) return
  try {
    const params = new URLSearchParams()
    for (const [k, v] of Object.entries(active)) {
      if (v) params.append(k, v)
    }
    const { data } = await api.get(`/core/question-graph/${props.graphCode}/visible-params/?${params}`)
    visibleParams.value = new Set(data.visible || [])
    for (const key of Object.keys(active)) {
      if (!visibleParams.value.has(key) && active[key]) {
        active[key] = ''
        emit('change', key, '')
      }
    }
  } catch (e) {
    visibleParams.value = null
  }
}, { deep: true })

</script>

<style scoped>
/* ── Bar root ── */
.eng-filter-bar {
  background: var(--cat-surface, #fff);
  border: 1px solid var(--cat-border, #e5e7eb);
  border-radius: var(--cat-radius-lg, 10px);
  padding: 12px 16px;
  margin-bottom: 20px;
}

/* ── Header ── */
.eng-filter-bar__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.eng-filter-bar__title {
  font-size: var(--cat-text-sm, 13px);
  font-weight: 600;
  color: var(--cat-muted, #6b7280);
  text-transform: uppercase;
  letter-spacing: .5px;
}
.eng-filter-bar__actions {
  display: flex;
  align-items: center;
  gap: 16px;
}
.eng-filter-bar__compat {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: var(--cat-text-sm, 13px);
  color: var(--cat-text, #1f2937);
}
.eng-filter-bar__compat input[type="checkbox"] {
  width: 15px; height: 15px; cursor: pointer;
}
.eng-filter-bar__reset {
  padding: 4px 12px;
  font-size: var(--cat-text-xs, 12px);
  background: var(--cat-bg, #f3f4f6);
  border: 1px solid var(--cat-border, #d1d5db);
  border-radius: var(--cat-radius-sm, 4px);
  cursor: pointer;
  color: var(--cat-muted, #6b7280);
}
.eng-filter-bar__reset:hover {
  background: var(--cat-border, #e5e7eb);
}

/* ── Grouped filter blocks (e.g. diameters) ── */
.eng-filter-bar__group {
  margin-bottom: 8px;
}
.eng-filter-bar__group .eng-filter-bar__chips {
  margin-bottom: 0;
}
.eng-filter-bar__group-label {
  display: block;
  font-size: var(--cat-text-xs, 11px);
  font-weight: 600;
  color: var(--cat-muted, #6b7280);
  text-transform: uppercase;
  letter-spacing: .5px;
  margin-bottom: 4px;
  padding-left: 2px;
}

/* ── Row 1: regular chips ── */
.eng-filter-bar__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: flex-end;
  margin-bottom: 8px;
}
.eng-filter-bar__chip {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.eng-filter-bar__chip-label {
  font-size: var(--cat-text-xs, 11px);
  color: var(--cat-muted, #9ca3af);
  padding-left: 2px;
}
.eng-filter-bar__chip-select {
  padding: 6px 10px;
  font-size: var(--cat-text-sm, 13px);
  color: var(--cat-text, #1f2937);
  border: 1px solid var(--cat-border, #d1d5db);
  border-radius: var(--cat-radius-md, 6px);
  background: var(--cat-surface, #fff);
  min-width: 120px;
  outline: none;
  cursor: pointer;
}
.eng-filter-bar__chip-select:focus {
  border-color: var(--cat-primary, #2563eb);
  box-shadow: 0 0 0 2px rgba(37, 99, 235, .1);
}
.eng-filter-bar__chip-input {
  padding: 6px 10px;
  font-size: var(--cat-text-sm, 13px);
  color: var(--cat-text, #1f2937);
  border: 1px solid var(--cat-border, #d1d5db);
  border-radius: var(--cat-radius-md, 6px);
  background: var(--cat-surface, #fff);
  min-width: 120px;
  outline: none;
}
.eng-filter-bar__chip-input:focus {
  border-color: var(--cat-primary, #2563eb);
  box-shadow: 0 0 0 2px rgba(37, 99, 235, .1);
}
.eng-filter-bar__chip-single {
  padding: 6px 10px;
  font-size: var(--cat-text-sm, 13px);
  color: var(--cat-text, #1f2937);
  background: var(--cat-bg, #f9fafb);
  border: 1px solid var(--cat-border, #d1d5db);
  border-radius: var(--cat-radius-md, 6px);
}

/* ── Row 2: special cascade filters (Exd + Climate) ── */
.eng-filter-bar__special {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .eng-filter-bar__chips { gap: 6px; }
  .eng-filter-bar__chip-select { min-width: 100px; font-size: var(--cat-text-xs, 12px); }
  .eng-filter-bar__special { grid-template-columns: 1fr; }
}
</style>
