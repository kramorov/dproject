<!-- apps/limit-switch-admin/App.vue — админка БКВ: табы Серии / Блоки -->
<template>
  <div class="lsb-admin">
    <header class="lsb-header">
      <h1>🔌 Блоки концевых выключателей</h1>
    </header>

    <div class="lsb-tabs">
      <button :class="{ act: tab === 'lines' }" @click="tab = 'lines'">Серии БКВ</button>
      <button :class="{ act: tab === 'boxes' }" @click="tab = 'boxes'">Блоки БКВ</button>
    </div>

    <!-- Серии БКВ -->
    <AdminTable v-if="tab === 'lines'"
      ref="linesTableRef"
      :columns="modelLineColumns"
      :fetchFn="modelLineApi.list"
      searchPlaceholder="Поиск по сериям..."
      createLabel="Серия"
      @select="onLineSelect"
      @create="onLineCreate"
    />

    <!-- Блоки БКВ -->
    <AdminTable v-if="tab === 'boxes'"
      ref="boxesTableRef"
      :columns="limitSwitchColumns"
      :fetchFn="limitSwitchApi.list"
      searchPlaceholder="Поиск по блокам..."
      createLabel="Блок"
      @select="onBoxSelect"
      @create="onBoxCreate"
    />


    <!-- Форма Серии -->
    <AdminForm
      :show="showLineForm"
      :title="lineFormTitle"
      :item="selectedLine"
      :api="modelLineApi"
      :formRef="lineFormRef"
      @saved="onLineSaved"
      @deleted="onLineSaved"
      @cancel="showLineForm = false"
    >
      <ModelLineForm ref="lineFormRef" :item="selectedLine" />
    </AdminForm>

    <!-- Форма Блока -->
    <AdminForm
      :show="showBoxForm"
      :title="boxFormTitle"
      :item="selectedBox"
      :api="limitSwitchApi"
      :formRef="boxFormRef"
      @saved="onBoxSaved"
      @deleted="onBoxSaved"
      @cancel="showBoxForm = false"
    >
      <LimitSwitchForm ref="boxFormRef" :item="selectedBox" />
    </AdminForm>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import AdminTable from './components/AdminTable.vue'
import AdminForm from './components/AdminForm.vue'
import ModelLineForm from './components/ModelLineForm.vue'
import LimitSwitchForm from './components/LimitSwitchForm.vue'
import { modelLineApi, limitSwitchApi } from './api'

const tab = ref('lines')

// ── Колонки таблиц ──
const modelLineColumns = [
  { key: 'name', label: 'Название' },
  { key: 'code', label: 'Код' },
]
const limitSwitchColumns = [
  { key: 'name', label: 'Название' },
  { key: 'code', label: 'Код' },
]

// ── Серии: состояние формы ──
const showLineForm = ref(false)
const selectedLine = ref(null)
const lineFormRef = ref(null)
const linesTableRef = ref(null)

const lineFormTitle = computed(() =>
  selectedLine.value?.id ? (selectedLine.value.name || 'Редактировать серию') : 'Новая серия БКВ'
)

async function onLineSelect(item) {
  try {
    const res = await modelLineApi.get(item.id)
    const full = res.data?.data || res.data
    selectedLine.value = full || item
  } catch { selectedLine.value = item }
  showLineForm.value = true
}
function onLineCreate() {
  selectedLine.value = null
  showLineForm.value = true
}
function onLineSaved() {
  showLineForm.value = false
  selectedLine.value = null
  nextTick(() => linesTableRef.value?.fetchData())
}

// ── Блоки: состояние формы ──
const showBoxForm = ref(false)
const selectedBox = ref(null)
const boxFormRef = ref(null)
const boxesTableRef = ref(null)

const boxFormTitle = computed(() =>
  selectedBox.value?.id ? (selectedBox.value.name || 'Редактировать блок') : 'Новый блок БКВ'
)

async function onBoxSelect(item) {
  try {
    const res = await limitSwitchApi.get(item.id)
    const full = res.data?.data || res.data
    selectedBox.value = full || item
  } catch { selectedBox.value = item }
  showBoxForm.value = true
}
function onBoxCreate() {
  selectedBox.value = null
  showBoxForm.value = true
}
function onBoxSaved() {
  showBoxForm.value = false
  selectedBox.value = null
  nextTick(() => boxesTableRef.value?.fetchData())
}
</script>

<style scoped>
.lsb-admin { max-width: 1300px; margin: 0 auto; padding: 20px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
.lsb-header { margin-bottom: 16px; }
.lsb-header h1 { margin: 0; font-size: 24px; }
.lsb-tabs { display: flex; gap: 4px; margin-bottom: 16px; }
.lsb-tabs button { padding: 6px 18px; border: 1px solid #d1d5db; border-radius: 6px; background: #fff; cursor: pointer; font-size: 14px; transition: all .15s; }
.lsb-tabs button.act { background: #2563eb; color: #fff; border-color: #2563eb; }
.lsb-tabs button:hover:not(.act) { background: #f3f4f6; }
.lsb-muted { color: #6b7280; font-size: 12px; }
</style>
