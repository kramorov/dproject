<!-- shared/components/FkSelect.vue — переиспользуемый выбор ForeignKey с поиском -->
<template>
  <div class="fk-select" ref="root">
    <label v-if="label" class="fk-label">{{ label }}</label>
    <div class="fk-input-wrap" @click="open = !open">
      <span v-if="selectedOption" class="fk-value">{{ selectedOption.name }}</span>
      <span v-else class="fk-placeholder">{{ placeholder || '—' }}</span>
      <button v-if="modelValue" class="fk-clear" @click.stop="clear">✕</button>
      <span class="fk-arrow">▾</span>
    </div>
    <div v-if="open" class="fk-drop">
      <input v-model="search" class="fk-search" placeholder="Поиск..." @click.stop ref="searchInput" />
      <div class="fk-list">
        <div v-for="opt in filteredOptions" :key="opt.id" class="fk-item"
          :class="{ sel: opt.id === modelValue }"
          @click.stop="select(opt)">
          {{ opt.name }}
        </div>
        <div v-if="!filteredOptions.length" class="fk-empty">Ничего не найдено</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({
  modelValue: { type: [Number, String], default: null },
  options: { type: Array, default: () => [] },
  placeholder: { type: String, default: '' },
  label: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const search = ref('')
const root = ref(null)
const searchInput = ref(null)

const selectedOption = computed(() =>
  props.options.find(o => o.id === props.modelValue) || null
)

const filteredOptions = computed(() => {
  if (!search.value) return props.options
  const q = search.value.toLowerCase()
  return props.options.filter(o => (o.name || '').toLowerCase().includes(q))
})

function select(opt) {
  emit('update:modelValue', opt.id)
  open.value = false
  search.value = ''
}

function clear() {
  emit('update:modelValue', null)
  search.value = ''
}

watch(open, async (v) => {
  if (v) { await nextTick(); searchInput.value?.focus() }
})

// Клик вне — закрыть
function onClickOutside(e) {
  if (root.value && !root.value.contains(e.target)) { open.value = false; search.value = '' }
}
import { onMounted, onUnmounted } from 'vue'
onMounted(() => document.addEventListener('click', onClickOutside))
onUnmounted(() => document.removeEventListener('click', onClickOutside))
</script>

<style scoped>
.fk-select { position: relative; min-width: 0; }
.fk-label { display: block; font-size: 13px; color: #374151; margin-bottom: 4px; }
.fk-input-wrap {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px;
  cursor: pointer; font-size: 13px; background: #fff; min-height: 34px;
}
.fk-input-wrap:hover { border-color: #9ca3af; }
.fk-value { flex: 1; color: #1f2937; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fk-placeholder { flex: 1; color: #9ca3af; }
.fk-clear { background: none; border: none; color: #9ca3af; cursor: pointer; font-size: 14px; padding: 0 2px; }
.fk-clear:hover { color: #dc2626; }
.fk-arrow { color: #9ca3af; font-size: 10px; }
.fk-drop {
  position: absolute; top: 100%; left: 0; right: 0; z-index: 50;
  background: #fff; border: 1px solid #d1d5db; border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0,0,0,.1); margin-top: 4px; max-height: 260px;
  display: flex; flex-direction: column;
}
.fk-search {
  padding: 6px 10px; border: none; border-bottom: 1px solid #e5e7eb;
  font-size: 13px; outline: none; border-radius: 6px 6px 0 0;
}
.fk-list { overflow-y: auto; flex: 1; }
.fk-item {
  padding: 6px 10px; font-size: 13px; cursor: pointer;
  transition: background .1s;
}
.fk-item:hover { background: #f0f9ff; }
.fk-item.sel { background: #eff6ff; color: #2563eb; font-weight: 500; }
.fk-empty { padding: 12px; font-size: 13px; color: #9ca3af; text-align: center; }
</style>
