<!-- shared/components/FilterSidebar.vue -->
<template>
  <aside class="filter-sidebar">
    <div class="filter-header">
      <h3>Фильтры</h3>
      <button class="reset-btn" @click="$emit('reset')" v-if="hasActive">Сбросить</button>
    </div>

    <div
      v-for="f in sortedFilters"
      :key="f.key"
      class="filter-group"
    >
      <!-- Exd-каскадный фильтр -->
      <ExdFilter
        v-if="f.filter_type === 'exd_compatible'"
        @update:modelValue="ids => onExdChange(ids)"
      />
      <!-- Обычные фильтры -->
      <template v-else>
        <label>{{ f.label }}</label>
        <span v-if="f.options.length === 1" class="filter-single-value">{{ f.options[0].name }}</span>
        <select v-else v-model="active[f.key]" @change="$emit('change', f.key, active[f.key])">
          <option value="">Все</option>
          <option
            v-for="opt in f.options"
            :key="opt.id"
            :value="opt.id"
          >{{ opt.name }}</option>
        </select>
      </template>
    </div>

    <div class="filter-group" v-if="showCompatibleToggle">
      <label class="compatible-label">
        <input type="checkbox" :checked="showCompatible" @change="$emit('toggleCompatible', $event.target.checked)" />
        Показывать совместимые
      </label>
    </div>

  </aside>
</template>

<script setup>
import { reactive, ref, computed, watch } from 'vue'
import ExdFilter from './ExdFilter.vue'

const activeExdIds = ref([])

const props = defineProps({
  filters: { type: Object, default: () => ({}) },
  showCompatible: { type: Boolean, default: false },
  showCompatibleToggle: { type: Boolean, default: false },
})

const emit = defineEmits(['change', 'reset', 'toggleCompatible'])

const active = reactive({})

// Синхронизация внешнего состояния с внутренним
watch(() => props.filters, (val) => {
  for (const [k, v] of Object.entries(val)) {
    active[k] = v
  }
}, { deep: true, immediate: true })

const sortedFilters = computed(() => {
  const arr = []
  for (const [key, val] of Object.entries(props.filters)) {
    if (val && val.options) arr.push({ key, ...val })
  }
  arr.sort((a, b) => (a.order || 99) - (b.order || 99))
  return arr
})

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
</script>

<style scoped>
.filter-sidebar { width: 260px; flex-shrink: 0; }
.filter-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.compatible-label { display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: var(--cat-text-base); color: var(--cat-text); }
.compatible-label input[type="checkbox"] { width: 16px; height: 16px; cursor: pointer; }
.filter-header h3 { font-size: var(--cat-text-xl); font-weight: 600; margin: 0; }
.reset-btn { padding: 4px 12px; font-size: var(--cat-text-sm); background: var(--cat-border-light); border: 1px solid var(--cat-border); border-radius: var(--cat-radius-sm); cursor: pointer; }
.reset-btn:hover { background: var(--cat-border); }
.filter-group { margin-bottom: 16px; }
.filter-group label { display: block; font-size: var(--cat-text-sm); font-weight: 500; color: var(--cat-muted); margin-bottom: 4px; }
.filter-group select { width: 100%; padding: 8px 10px; font-size: var(--cat-text-base); color: var(--cat-text); border: 1px solid var(--cat-border); border-radius: var(--cat-radius-md); background: var(--cat-surface); }
.filter-single-value { display: block; padding: 8px 10px; font-size: var(--cat-text-base); color: var(--cat-text); background: var(--cat-surface); border: 1px solid var(--cat-border); border-radius: var(--cat-radius-md); }
</style>