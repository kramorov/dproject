<!-- shared/components/M2MDualList.vue — filter_horizontal style M2M selector -->
<template>
  <div class="mdl-wrap">
    <label class="mdl-label">{{ label }}</label>
    <div class="mdl-body">
      <!-- Available -->
      <div class="mdl-pane">
        <div class="mdl-pane-title">Доступно</div>
        <input v-model="filterAvailable" class="mdl-search" placeholder="Поиск..." />
        <select multiple class="mdl-list" ref="availableRef"
          @dblclick="moveRight" size="8">
          <option v-for="opt in filteredAvailable" :key="opt.id" :value="opt.id">{{ opt.name }}</option>
        </select>
      </div>

      <!-- Buttons -->
      <div class="mdl-btns">
        <button @click="moveRight" :disabled="!hasAvailable" title="Выбрать">→</button>
        <button @click="moveLeft" :disabled="!hasSelected" title="Убрать">←</button>
      </div>

      <!-- Selected -->
      <div class="mdl-pane">
        <div class="mdl-pane-title">Выбрано</div>
        <input v-model="filterSelected" class="mdl-search" placeholder="Поиск..." />
        <select multiple class="mdl-list" ref="selectedRef"
          @dblclick="moveLeft" size="8">
          <option v-for="s in filteredSelected" :key="s.id" :value="s.id">{{ s.name }}</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  options: { type: Array, default: () => [] },          // [{id, name}]
  label: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const filterAvailable = ref('')
const filterSelected = ref('')
const availableRef = ref(null)
const selectedRef = ref(null)

const selectedIds = computed(() => new Set(props.modelValue))

const selectedItems = computed(() =>
  props.options.filter(o => selectedIds.value.has(o.id))
)

const availableItems = computed(() =>
  props.options.filter(o => !selectedIds.value.has(o.id))
)

const filteredAvailable = computed(() => {
  const q = filterAvailable.value.toLowerCase()
  return q ? availableItems.value.filter(o => o.name.toLowerCase().includes(q)) : availableItems.value
})

const filteredSelected = computed(() => {
  const q = filterSelected.value.toLowerCase()
  return q ? selectedItems.value.filter(o => o.name.toLowerCase().includes(q)) : selectedItems.value
})

const hasAvailable = computed(() => filteredAvailable.value.length > 0)
const hasSelected = computed(() => filteredSelected.value.length > 0)

function moveRight() {
  const sel = availableRef.value
  if (!sel || sel.selectedOptions.length === 0) return
  const ids = Array.from(sel.selectedOptions, o => parseInt(o.value))
  emit('update:modelValue', [...props.modelValue, ...ids])
}

function moveLeft() {
  const sel = selectedRef.value
  if (!sel || sel.selectedOptions.length === 0) return
  const ids = new Set(Array.from(sel.selectedOptions, o => parseInt(o.value)))
  emit('update:modelValue', props.modelValue.filter(id => !ids.has(id)))
}
</script>

<style scoped>
.mdl-wrap { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.mdl-label { font-size: 13px; color: #374151; }
.mdl-body { display: flex; gap: 8px; align-items: stretch; }
.mdl-pane { flex: 1; display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.mdl-pane-title { font-size: 11px; color: #6b7280; font-weight: 500; }
.mdl-search { padding: 4px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 12px; }
.mdl-list {
  flex: 1; min-height: 140px; border: 1px solid #d1d5db; border-radius: 4px;
  font-size: 12px; padding: 2px; overflow-y: auto;
}
.mdl-list option { padding: 3px 6px; cursor: pointer; }
.mdl-list option:checked { background: #2563eb; color: #fff; }
.mdl-btns { display: flex; flex-direction: column; justify-content: center; gap: 8px; flex-shrink: 0; }
.mdl-btns button {
  padding: 4px 10px; border: 1px solid #d1d5db; border-radius: 4px;
  background: #fff; cursor: pointer; font-size: 14px;
}
.mdl-btns button:disabled { opacity: .3; cursor: default; }
.mdl-btns button:not(:disabled):hover { background: #f3f4f6; }
</style>
