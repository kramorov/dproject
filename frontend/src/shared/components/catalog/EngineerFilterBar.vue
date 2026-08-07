<!-- shared/components/catalog/EngineerFilterBar.vue -->
<!-- Horizontal filter bar for EngineerSelection. Row 1: regular selects, Row 2: Exd + Climate. -->
<template>
  <div class="eng-filter-bar">
    <!-- Header row: title + actions -->
    <div class="eng-filter-bar__header">
      <span class="eng-filter-bar__title">Фильтры</span>
      <div class="eng-filter-bar__actions">
        <label class="eng-filter-bar__compat" v-if="showCompatibleToggle">
          <input type="checkbox" :checked="showCompatible" @change="$emit('toggleCompatible', $event.target.checked)" />
          Совместимые
        </label>
        <button class="eng-filter-bar__reset" @click="$emit('reset')" v-if="hasActive">Сбросить</button>
      </div>
    </div>

    <!-- Row 1: regular filter selects -->
    <div class="eng-filter-bar__chips" v-if="regularFilters.length">
      <!-- Thread combined filter (type + size) -->
      <div v-if="hasThreadPair" class="eng-filter-bar__chip eng-filter-bar__thread">
        <ThreadFilter @change="onThreadChange" />
      </div>
      <div v-for="f in regularFilters" :key="f.key" class="eng-filter-bar__chip" v-show="!isThreadFilter(f.key) && isVisible(f.key)">
        <label class="eng-filter-bar__chip-label">{{ f.label }}</label>
        <span v-if="f.options.length === 1" class="eng-filter-bar__chip-single">{{ f.options[0].name }}</span>
        <select
          v-else
          class="eng-filter-bar__chip-select"
          v-model="active[f.key]"
          @change="$emit('change', f.key, active[f.key])"
        >
          <option value="">Не указано</option>
          <option v-for="opt in f.options" :key="opt.id" :value="opt.id">{{ f.show_code && opt.code ? opt.code + ' ' + opt.name : opt.name }}</option>
        </select>
      </div>
    </div>

    <!-- Row 2: Exd + Climate (special cascade filters) -->
    <div class="eng-filter-bar__special" v-if="specialFilters.length">
      <div v-for="f in specialFilters" :key="f.key" class="eng-filter-bar__special-item">
        <ExdFilter
          v-if="f.filter_type === 'exd_compatible'"
          @update:modelValue="ids => onExdChange(ids)"
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

const regularFilters = computed(() =>
  allFilters.value.filter(f =>
    f.filter_type !== 'exd_compatible' && f.filter_type !== 'climate_cascade'
  )
)

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

const THREAD_KEYS = ['thread_type_id', 'thread_id']
const hasThreadPair = computed(() => THREAD_KEYS.every(k => k in props.filters))
function isThreadFilter(key) { return THREAD_KEYS.includes(key) }
function onThreadChange(v) { if (v.thread_type_id != null) emit('change', 'thread_type_id', v.thread_type_id); if (v.thread_id != null) emit('change', 'thread_id', v.thread_id) }

function onClimateChange(temps, key) {
  if (temps) {
    emit('change', 'work_temp_min', temps.min_temp)
    emit('change', 'work_temp_max', temps.max_temp)
  }
}
import api from '@/shared/api'

const visibleParams = ref(null)
function isVisible(key) {
  if (visibleParams.value === null) return true
  if (THREAD_KEYS.includes(key)) return hasThreadPair.value && visibleParams.value.has(key)
  return visibleParams.value.has(key)
}

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
