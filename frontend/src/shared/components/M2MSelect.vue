<!-- shared/components/M2MSelect.vue — переиспользуемый выбор ManyToMany с чипсами -->
<template>
  <div class="m2m-select" ref="root">
    <label v-if="label" class="m2m-label">{{ label }}</label>
    <div class="m2m-chips-wrap" @click="open = !open">
      <span v-for="id in modelValue" :key="id" class="m2m-chip">
        {{ getOptionName(id) }}
        <button class="m2m-chip-x" @click.stop="remove(id)">✕</button>
      </span>
      <span v-if="!modelValue.length" class="m2m-placeholder">{{ placeholder || '—' }}</span>
      <span class="m2m-arrow">▾</span>
    </div>
    <div v-if="open" class="m2m-drop">
      <input v-model="search" class="m2m-search" placeholder="Поиск..." @click.stop ref="searchInput" />
      <div class="m2m-list">
        <div v-for="opt in availableOptions" :key="opt.id" class="m2m-item"
          @click.stop="add(opt)">
          <span class="m2m-check">{{ modelValue.includes(opt.id) ? '☑' : '☐' }}</span>
          {{ opt.name }}
        </div>
        <div v-if="!availableOptions.length" class="m2m-empty">Ничего не найдено</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  options: { type: Array, default: () => [] },
  placeholder: { type: String, default: '' },
  label: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const search = ref('')
const root = ref(null)
const searchInput = ref(null)

function getOptionName(id) {
  return props.options.find(o => o.id === id)?.name || String(id)
}

const availableOptions = computed(() => {
  const q = search.value.toLowerCase()
  return props.options.filter(o => {
    if (q && !(o.name || '').toLowerCase().includes(q)) return false
    return true
  })
})

function add(opt) {
  const arr = [...props.modelValue]
  if (arr.includes(opt.id)) {
    emit('update:modelValue', arr.filter(id => id !== opt.id))
  } else {
    arr.push(opt.id)
    emit('update:modelValue', arr)
  }
}

function remove(id) {
  emit('update:modelValue', props.modelValue.filter(x => x !== id))
}

watch(open, async (v) => {
  if (v) { await nextTick(); searchInput.value?.focus() }
})

function onClickOutside(e) {
  if (root.value && !root.value.contains(e.target)) { open.value = false; search.value = '' }
}
onMounted(() => document.addEventListener('click', onClickOutside))
onUnmounted(() => document.removeEventListener('click', onClickOutside))
</script>

<style scoped>
.m2m-select { position: relative; min-width: 0; }
.m2m-label { display: block; font-size: 13px; color: #374151; margin-bottom: 4px; }
.m2m-chips-wrap {
  display: flex; flex-wrap: wrap; align-items: center; gap: 4px;
  padding: 4px 8px; border: 1px solid #d1d5db; border-radius: 6px;
  cursor: pointer; font-size: 13px; background: #fff; min-height: 34px;
}
.m2m-chips-wrap:hover { border-color: #9ca3af; }
.m2m-chip {
  display: inline-flex; align-items: center; gap: 2px;
  padding: 2px 6px; background: #eff6ff; color: #2563eb;
  border-radius: 4px; font-size: 12px; white-space: nowrap; max-width: 180px;
  overflow: hidden; text-overflow: ellipsis;
}
.m2m-chip-x { background: none; border: none; color: #6b7280; cursor: pointer; font-size: 10px; padding: 0 1px; }
.m2m-chip-x:hover { color: #dc2626; }
.m2m-placeholder { flex: 1; color: #9ca3af; }
.m2m-arrow { color: #9ca3af; font-size: 10px; margin-left: auto; }
.m2m-drop {
  position: absolute; top: 100%; left: 0; right: 0; z-index: 50;
  background: #fff; border: 1px solid #d1d5db; border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0,0,0,.1); margin-top: 4px; max-height: 260px;
  display: flex; flex-direction: column;
}
.m2m-search {
  padding: 6px 10px; border: none; border-bottom: 1px solid #e5e7eb;
  font-size: 13px; outline: none; border-radius: 6px 6px 0 0;
}
.m2m-list { overflow-y: auto; flex: 1; }
.m2m-item {
  padding: 6px 10px; font-size: 13px; cursor: pointer;
  display: flex; align-items: center; gap: 6px;
  transition: background .1s;
}
.m2m-item:hover { background: #f0f9ff; }
.m2m-check { font-size: 12px; width: 16px; text-align: center; }
.m2m-empty { padding: 12px; font-size: 13px; color: #9ca3af; text-align: center; }
</style>
