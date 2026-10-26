<template>
  <div class="ec-conf">
    <h2>Конфигуратор БУ (тестовый)</h2>

    <div class="selects">
      <label>Серия
        <select v-model="modelLine" @change="onContextChange">
          <option :value="null">— серия —</option>
          <option v-for="m in meta.model_lines" :key="m.id" :value="m.id">{{ m.code }}</option>
        </select>
      </label>
      <label>Напряжение
        <select v-model="powerSupply" @change="onContextChange">
          <option :value="null">— напряжение —</option>
          <option v-for="p in meta.power_supplies" :key="p.id" :value="p.id">{{ p.code }}</option>
        </select>
      </label>
      <label>Блок управления
        <select v-model="unitId" @change="onUnitChange" :disabled="!seriesUnits.length">
          <option :value="null">— БУ —</option>
          <option v-for="u in seriesUnits" :key="u.unit_id" :value="u.unit_id">
            {{ u.name }} ({{ u.encoding }}){{ u.is_default ? ' · по умолчанию' : '' }}
          </option>
        </select>
      </label>
      <span v-if="error" class="error">{{ error }}</span>
    </div>

    <div v-if="pkg" class="content">
      <div class="unit-card">
        <h3>{{ pkg.unit.name }} <small>{{ pkg.unit.kind_display }}</small></h3>
        <p class="desc">{{ pkg.unit.description }}</p>
        <table v-if="pkg.unit.spec" class="spec">
          <tbody>
            <template v-for="(fields, section) in pkg.unit.spec" :key="section">
              <tr><th colspan="2">{{ section }}</th></tr>
              <tr v-for="(value, label) in fields" :key="label">
                <td>{{ label }}</td><td>{{ value }}</td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <div v-for="section in sectionTree" :key="section.code" class="section">
        <h4>{{ section.name }}</h4>
        <template v-for="slot in slotsOf(section)" :key="slot.code">
          <div v-if="slotState(slot.code).visible" class="slot"
               :class="{ blocked: slotState(slot.code).blocked }">
            <div class="slot-head">
              <strong>{{ slot.name }}</strong>
              <span class="mode">{{ slot.selection_mode }}</span>
              <span v-if="slot.required || slotState(slot.code).required" class="req">обязателен</span>
            </div>
            <div class="opts">
              <label v-for="o in slot.options" :key="o.code"
                     :class="['opt', { na: o.availability === null, std: o.availability === 'std' }]">
                <input v-if="slot.selection_mode === 'multi'" type="checkbox"
                       :disabled="o.availability === null || slotState(slot.code).blocked"
                       :checked="(selection[slot.code] || []).includes(o.code)"
                       @change="toggleOption(slot, o)" />
                <input v-else type="radio" :name="slot.code"
                       :disabled="o.availability === null || slotState(slot.code).blocked"
                       :checked="selection[slot.code] === o.code"
                       @change="selectOption(slot, o)" />
                <span class="name">{{ o.name }}</span>
                <span v-if="o.availability" class="avail">{{ o.availability }}</span>
                <span v-if="o.bundle" class="bundle" :title="'Пакет ' + o.bundle">⧉{{ o.bundle }}</span>
              </label>
            </div>
          </div>
        </template>
      </div>

      <div class="result">
        <h4>Результат</h4>
        <p><strong>Артикул:</strong> <code>{{ article }}</code></p>
        <p><strong>Снимок:</strong></p>
        <pre>{{ snapshot }}</pre>
        <ul v-if="errors.length" class="errors">
          <li v-for="e in errors" :key="e">{{ e }}</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * Тестовый конфигуратор БУ: серия → напряжение → тип БУ → пакет конфигурации.
 *
 * Пакет (/api/ea-control/package/) — серверный источник истины: доступность
 * опций (Паттерн А), дефолты профиля и правила (Паттерн В) резолвятся на
 * бэке; фронт применяет правила к видимости, ведёт выбор, показывает снимок
 * и собранный артикул. Конфликты/пакеты подсвечиваются списком ошибок.
 */
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/shared/api'

const route = useRoute()
const locale = computed(() => route.meta.locale || 'ru')

const meta = reactive({ model_lines: [], power_supplies: [] })
const modelLine = ref(null)
const powerSupply = ref(null)
const unitId = ref(null)
const seriesUnits = ref([])
const pkg = ref(null)
const selection = reactive({})
const error = ref('')
// выбранная схема цепей (опция слота CMD_WIRING): по ней сервер
// перерезолвивает набор сигналов дистанционного управления
const wiringSignalPowerId = ref(null)

const errors = computed(() => {
  if (!pkg.value) return []
  const out = []
  const selectedOptions = new Set()
  for (const slot of pkg.value.slots) {
    const v = selection[slot.code]
    for (const o of slot.options) {
      const chosen = Array.isArray(v) ? v.includes(o.code) : v === o.code
      if (chosen && o.availability !== null) selectedOptions.add(o)
    }
  }
  for (const o of selectedOptions) {
    for (const c of o.conflicts || []) {
      for (const q of selectedOptions) {
        if (q.code === c) out.push(`Конфликт: ${o.name} ↔ ${q.name}`)
      }
    }
    if (o.bundle) {
      const members = []
      for (const slot of pkg.value.slots) {
        for (const x of slot.options) {
          if (x.bundle === o.bundle && x.availability !== null) members.push(x)
        }
      }
      const missing = members.filter(x => !selectedOptions.has(x))
      if (missing.length) {
        out.push(`Пакет ${o.bundle}: не выбраны ${missing.map(x => x.name).join(', ')}`)
      }
    }
  }
  return out
})

const snapshot = computed(() => {
  const out = {}
  for (const slot of pkg.value?.slots || []) {
    if (selection[slot.code] !== undefined && selection[slot.code] !== null) {
      out[slot.code] = selection[slot.code]
    }
  }
  return JSON.stringify(out, null, 2)
})

const article = computed(() => {
  if (!pkg.value) return ''
  const unit = seriesUnits.value.find(u => u.unit_id === unitId.value)
  const parts = [unit?.encoding || pkg.value.unit.code]
  for (const slot of pkg.value.slots) {
    const v = selection[slot.code]
    for (const o of slot.options) {
      const chosen = Array.isArray(v) ? v.includes(o.code) : v === o.code
      if (chosen && o.ext_encoding) parts.push(o.ext_encoding)
    }
  }
  return parts.join('')
})

const sectionTree = computed(() => {
  if (!pkg.value) return []
  const byCode = {}
  for (const s of pkg.value.sections) byCode[s.code] = { ...s, children: [] }
  const roots = []
  for (const node of Object.values(byCode)) {
    if (node.parent_code && byCode[node.parent_code]) {
      byCode[node.parent_code].children.push(node)
    } else {
      roots.push(node)
    }
  }
  return roots
})

function slotsOf(section) {
  return (pkg.value.slots || []).filter(s => s.section_code === section.code)
}

function slotState(slotCode) {
  if (!pkg.value) return { visible: true, blocked: false, required: false, default: null }
  const value = selection['control_unit']
  const rules = pkg.value.rules.filter(r => r.target_slot === slotCode)
  const state = { visible: true, blocked: false, required: false, default: null }
  for (const r of [...rules].sort((a, b) => (a.priority - b.priority) || (a.id - b.id))) {
    const current = r.when_slot === 'control_unit' ? value : selection[r.when_slot]
    if (!evaluate(r.operator, r.when_value, current)) continue
    if (r.action === 'show') state.visible = true
    else if (r.action === 'hide') state.visible = false
    else if (r.action === 'block') state.blocked = true
    else if (r.action === 'require') state.required = true
    else if (r.action === 'set_default') state.default = r.action_value
  }
  return state
}

function evaluate(op, expected, current) {
  if (op === 'is_set') return current !== null && current !== undefined && current !== ''
  if (op === 'not_exact') return current !== expected
  if (op === 'icontains') return String(current || '').includes(String(expected || ''))
  if (op === 'gte') return Number(current) >= Number(expected)
  if (op === 'lte') return Number(current) <= Number(expected)
  if (op === 'in') return Array.isArray(expected) && expected.includes(current)
  if (op === 'not_in') return Array.isArray(expected) && !expected.includes(current)
  return current === expected
}

function selectOption(slot, o) {
  selection[slot.code] = o.code
  if (slot.code === 'CMD_WIRING' && o.signal_power_id
      && o.signal_power_id !== wiringSignalPowerId.value) {
    reloadPackageForWiring(o.signal_power_id).catch(e => { error.value = e.displayMessage })
    return
  }
  applySetDefaults()
}

function toggleOption(slot, o) {
  const arr = selection[slot.code] ? [...selection[slot.code]] : []
  const i = arr.indexOf(o.code)
  if (i >= 0) arr.splice(i, 1)
  else arr.push(o.code)
  selection[slot.code] = arr
  applySetDefaults()
}

function applySetDefaults() {
  if (!pkg.value) return
  for (const slot of pkg.value.slots) {
    const state = slotState(slot.code)
    if (state.default !== null && selection[slot.code] === undefined) {
      selection[slot.code] = state.default
    }
  }
}

function applyProfileDefaults() {
  for (const [slotCode, optionCode] of Object.entries(pkg.value.defaults || {})) {
    if (selection[slotCode] === undefined) selection[slotCode] = optionCode
  }
  for (const slot of pkg.value.slots) {
    if (selection[slot.code] === undefined) {
      const def = slot.options.find(o => o.is_default && o.availability !== null)
      if (def) selection[slot.code] = def.code
    }
  }
}

async function loadMeta() {
  const { data } = await api.get('/ea-control/meta/')
  meta.model_lines = data.model_lines || []
  meta.power_supplies = data.power_supplies || []
}

async function loadSeriesUnits() {
  seriesUnits.value = []
  unitId.value = null
  pkg.value = null
  if (!modelLine.value) return
  const { data } = await api.get('/ea-control/series-units/', {
    params: {
      model_line: modelLine.value,
      power_supply: powerSupply.value || undefined,
      locale: locale.value,
    },
  })
  seriesUnits.value = data || []
}

async function loadPackage() {
  pkg.value = null
  wiringSignalPowerId.value = null
  for (const k of Object.keys(selection)) delete selection[k]
  if (!unitId.value) return
  const { data } = await api.get('/ea-control/package/', {
    params: {
      unit: unitId.value,
      model_line: modelLine.value || undefined,
      power_supply: powerSupply.value || undefined,
      locale: locale.value,
    },
  })
  pkg.value = data
  // значение слота control_unit в снимке/правилах — код ОПЦИИ (CU_BASIC…),
  // а не код типа БУ (basic…) — их разводит резолвер (option_code)
  selection['control_unit'] = (seriesUnits.value.find(u => u.unit_id === unitId.value)
                               || {}).option_code || null
  applyProfileDefaults()
}

async function reloadPackageForWiring(signalPowerId) {
  // схема цепей выбрана → перерезолвить набор сигналов на сервере
  const keep = { ...selection }
  const { data } = await api.get('/ea-control/package/', {
    params: {
      unit: unitId.value,
      model_line: modelLine.value || undefined,
      power_supply: powerSupply.value || undefined,
      signal_power: signalPowerId || undefined,
      locale: locale.value,
    },
  })
  wiringSignalPowerId.value = signalPowerId
  pkg.value = data
  for (const k of Object.keys(selection)) delete selection[k]
  Object.assign(selection, keep)
  applyProfileDefaults()
}

function onContextChange() {
  loadSeriesUnits().catch(e => { error.value = e.displayMessage })
}

function onUnitChange() {
  loadPackage().catch(e => { error.value = e.displayMessage })
}

watch(locale, () => {
  if (unitId.value) loadPackage().catch(() => {})
})

onMounted(async () => {
  try {
    await loadMeta()
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка загрузки справочников'
  }
})
</script>

<style scoped>
.ec-conf { padding: 16px; max-width: 1100px; }
.selects { display: flex; gap: 16px; align-items: end; margin-bottom: 16px; flex-wrap: wrap; }
.selects label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; }
.selects select { padding: 4px 6px; min-width: 180px; }
.error { color: #c00; }
.content { display: flex; flex-direction: column; gap: 14px; }
.unit-card { border: 1px solid #ddd; border-radius: 6px; padding: 12px; }
.unit-card h3 { margin: 0 0 6px; }
.desc { color: #444; margin: 0 0 8px; }
.spec { border-collapse: collapse; font-size: 13px; }
.spec th, .spec td { border: 1px solid #eee; padding: 3px 8px; text-align: left; }
.section { border: 1px solid #e0e0e0; border-radius: 6px; padding: 10px; }
.section h4 { margin: 0 0 8px; }
.slot { margin-bottom: 10px; }
.slot.blocked { opacity: .55; }
.slot-head { display: flex; gap: 8px; align-items: baseline; margin-bottom: 4px; }
.mode { color: #888; font-size: 12px; }
.req { color: #b60; font-size: 12px; }
.opts { display: flex; flex-wrap: wrap; gap: 8px; }
.opt { display: flex; gap: 6px; align-items: center; border: 1px solid #ddd; border-radius: 4px; padding: 4px 8px; font-size: 13px; }
.opt.na { opacity: .4; }
.opt.std { border-color: #7ab07a; background: #f2faf2; }
.name { }
.avail { color: #999; font-size: 11px; }
.bundle { color: #2c6fb0; font-size: 11px; cursor: help; }
.result { border: 1px solid #ccc; border-radius: 6px; padding: 12px; background: #fafafa; }
.result pre { background: #fff; border: 1px solid #eee; padding: 8px; font-size: 12px; }
.errors { color: #c00; }
</style>
