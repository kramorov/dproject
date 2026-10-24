<template>
  <div class="describe">
    <div class="toolbar">
      <select v-model="unitId" @change="load">
        <option :value="null" disabled>— выберите БУ —</option>
        <option v-for="u in units" :key="u.id" :value="u.id">{{ u.name }} ({{ u.code }})</option>
      </select>
      <button :disabled="!text" @click="copyText">Копировать текст</button>
    </div>
    <div v-if="error" class="error-banner">{{ error }}</div>

    <div v-if="report" class="report">
      <div class="unit-head">
        <h3>{{ report.unit.name }} ({{ report.unit.code }})</h3>
        <span>{{ [report.unit.kind_display, report.unit.brand_name,
                  report.unit.location, report.unit.control_voltage]
                  .filter(Boolean).join(' · ') }}</span>
      </div>

      <div v-for="sec in report.sections" :key="sec.code || sec.name" class="sec"
           :style="{ paddingLeft: (sec.depth * 16) + 'px' }">
        <h4>{{ sec.name }}</h4>
        <div v-for="slot in sec.slots" :key="slot.code" class="slot">
          <div class="slot-name">{{ slot.name }} <span class="code">{{ slot.code }}</span></div>
          <div class="cells">
            <span v-for="o in slot.options" :key="o.code" class="cell"
                  :class="'av-' + o.availability">
              {{ o.name }} <i>[{{ mark(o.availability) }}]</i>
            </span>
          </div>
        </div>
      </div>
    </div>

    <div class="legend">[st] — стандарт · [op] — опция · [na] — недоступно</div>
    <pre v-if="text" class="text">{{ text }}</pre>
  </div>
</template>

<script setup>
/**
 * Описание БУ для проверки производителем: все слоты, сгруппированные по
 * узлам; каждая опция — ячейка с доступностью (std/opt/na). Текстовая
 * версия для отправки формируется кнопкой «Копировать текст».
 */
import { onMounted, ref } from 'vue'
import api from '@/shared/api'

const units = ref([])
const unitId = ref(null)
const report = ref(null)
const text = ref('')
const error = ref('')

const AVAIL = { std: 'st', opt: 'op', na: 'na' }
function mark(a) {
  return AVAIL[a] || a
}

function buildText() {
  const r = report.value
  if (!r) return ''
  const lines = []
  lines.push(`Описание блока управления: ${r.unit.name} (${r.unit.code})`)
  lines.push([r.unit.kind_display, r.unit.brand_name, r.unit.location,
              r.unit.control_voltage].filter(Boolean).join(' · '))
  for (const sec of r.sections) {
    if (!sec.slots.length) continue
    const indent = '  '.repeat(sec.depth)
    lines.push('')
    lines.push(`${indent}== ${sec.name} ==`)
    for (const slot of sec.slots) {
      const cells = slot.options
        .map(o => `${o.name} [${mark(o.availability)}]`).join(' | ')
      lines.push(`${indent}${slot.name}: ${cells}`)
    }
  }
  return lines.join('\n')
}

async function load() {
  if (!unitId.value) return
  error.value = ''
  try {
    const { data } = await api.get(`/ea-control/describe/?unit=${unitId.value}`)
    report.value = data
    text.value = buildText()
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка загрузки описания'
  }
}

async function copyText() {
  try {
    await navigator.clipboard.writeText(text.value)
  } catch (e) {
    error.value = 'Не удалось скопировать (clipboard недоступен)'
  }
}

onMounted(async () => {
  try {
    const { data } = await api.get('/ea-control/units/')
    units.value = Array.isArray(data) ? data : []
    if (units.value.length) {
      unitId.value = units.value[0].id
      await load()
    }
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка загрузки БУ'
  }
})
</script>

<style scoped>
.describe { padding: 4px 0; }
.toolbar { display: flex; gap: 8px; align-items: center; margin-bottom: 10px; }
.toolbar select { padding: 6px 8px; min-width: 240px; }
.toolbar button { padding: 6px 14px; cursor: pointer; }
.error-banner { background: #fdecea; color: #c62828; padding: 8px 10px; border-radius: 4px; margin-bottom: 10px; }
.unit-head { margin-bottom: 12px; }
.unit-head h3 { margin: 0 0 2px; }
.unit-head span { color: #666; font-size: 13px; }
.sec { margin-bottom: 12px; }
.sec h4 { margin: 0 0 4px; }
.slot { margin-bottom: 8px; }
.slot-name { font-size: 13px; color: #333; margin-bottom: 3px; }
.slot-name .code { color: #888; font-size: 11px; }
.cells { display: flex; flex-wrap: wrap; gap: 4px; }
.cell { border: 1px solid #ccc; border-radius: 4px; padding: 2px 8px; font-size: 12px; }
.cell i { color: #555; font-style: normal; }
.av-std { background: #e8f5e9; border-color: #a5d6a7; }
.av-opt { background: #fff8e1; border-color: #ffe082; }
.av-na { background: #f5f5f5; border-color: #e0e0e0; color: #999; }
.av-na i { color: #bdbdbd; }
.legend { color: #666; font-size: 12px; margin: 6px 0; }
.text { background: #fafafa; border: 1px solid #ddd; border-radius: 4px; padding: 10px; font-size: 12px; white-space: pre-wrap; }
</style>
