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
      <label>{{ f.label }}</label>
      <!-- Одна опция — показываем текстом -->
      <span v-if="f.options.length === 1" class="filter-single-value">{{ f.options[0].name }}</span>
      <!-- Несколько опций — выпадающий список -->
      <select v-else v-model="active[f.key]" @change="$emit('change', f.key, active[f.key])">
        <option value="">Все</option>
        <option
          v-for="opt in f.options"
          :key="opt.id"
          :value="opt.id"
        >{{ opt.name }}</option>
      </select>
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
import { reactive, computed, watch } from 'vue'

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
.filter-group select { width: 100%; padding: 8px 10px; font-size: var(--cat-text-base); border: 1px solid var(--cat-border); border-radius: var(--cat-radius-md); background: var(--cat-surface); }
.filter-single-value { display: block; padding: 8px 10px; font-size: var(--cat-text-base); color: var(--cat-text); background: var(--cat-surface); border: 1px solid var(--cat-border); border-radius: var(--cat-radius-md); }
</style>