<template>
  <div class="tf-root">
    <label class="tf-label">{{ label || 'Резьба' }}</label>
    <div class="tf-row">
      <!-- Тип резьбы -->
      <select
        class="tf-select"
        :value="selectedThreadType"
        @change="onTypeChange($event.target.value)"
      >
        <option :value="null">Все типы</option>
        <option
          v-for="tt in types"
          :key="tt.id"
          :value="tt.id"
        >{{ tt.name }}</option>
      </select>

      <!-- Размер резьбы -->
      <select
        class="tf-select tf-size"
        :value="selectedThreadId"
        @change="onSizeChange($event.target.value)"
      >
        <option :value="null">Все размеры</option>
        <option
          v-for="ts in filteredSizes"
          :key="ts.id"
          :value="ts.id"
        >{{ ts.name }}</option>
      </select>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/shared/api'

const props = defineProps({
  modelValue: { type: Object, default: () => ({ thread_type_id: null, thread_id: null }) },
  label: { type: String, default: 'Резьба' },
  equipmentTypeCode: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'change'])

const types = ref([])
const sizes = ref([])          // all sizes (full list)
const filteredSizes = ref([])  // scoped by type
const selectedThreadType = ref(props.modelValue.thread_type_id || null)
const selectedThreadId = ref(props.modelValue.thread_id || null)

// Map size_id → thread_type_id for auto-population
const sizeToTypeMap = ref({})

onMounted(async () => {
  try {
    const { data } = await api.get('/core/thread-filter-options/')
    types.value = data.types || []
    sizes.value = data.sizes || []
    filteredSizes.value = data.sizes || []

    // Build reverse map: size_id -> thread_type_id
    for (const s of data.sizes) {
      if (s.thread_type_id) {
        sizeToTypeMap.value[s.id] = s.thread_type_id
      }
    }
  } catch (e) {
    console.error('ThreadFilter: failed to load options', e)
  }
})

watch(() => props.modelValue, (v) => {
  if (v) {
    selectedThreadType.value = v.thread_type_id || null
    selectedThreadId.value = v.thread_id || null
  }
})

function onTypeChange(typeId) {
  const tId = typeId === '' ? null : Number(typeId)
  selectedThreadType.value = tId

  if (tId) {
    // Filter sizes by type
    filteredSizes.value = sizes.value.filter(s => s.thread_type_id === tId)
  } else {
    filteredSizes.value = sizes.value
    // Clear size if no type — or keep? Keep as-is.
  }
  emitAll()
}

function onSizeChange(sizeId) {
  const sId = sizeId === '' ? null : Number(sizeId)
  selectedThreadId.value = sId

  // Auto-populate type from selected size
  if (sId && !selectedThreadType.value) {
    selectedThreadType.value = sizeToTypeMap.value[sId] || null
  }
  emitAll()
}

function emitAll() {
  const v = {
    thread_type_id: selectedThreadType.value,
    thread_id: selectedThreadId.value,
  }
  emit('update:modelValue', v)
  emit('change', v)
}
</script>

<style scoped>
.tf-root { margin-bottom: 0.5rem; }
.tf-label { display: block; font-weight: 600; margin-bottom: 0.25rem; font-size: 0.9rem; color: #555; }
.tf-row { display: flex; gap: 0.5rem; }
.tf-select { padding: 0.5rem; border: 1px solid #ddd; border-radius: 6px; font-size: 0.9rem; background: #fff; flex: 1; }
.tf-size { flex: 2; }
</style>
