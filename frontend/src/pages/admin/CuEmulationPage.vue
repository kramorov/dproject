<template>
  <div class="cu-emu">
    <h2>Эмуляция конфигуратора опций БУ</h2>
    <p class="hint">
      Выбор БУ → страница опций по его настройкам (правила show/hide, доступность
      std/opt). Можно поменять любую опцию на другую разрешённую и посмотреть
      спецификацию/описание модификации (генератор cu_description).
    </p>

    <div class="selects">
      <label>Блок управления
        <select v-model="unitId" @change="onUnitChange">
          <option :value="null">— БУ —</option>
          <option v-for="u in units" :key="u.id" :value="u.id">
            {{ u.name }} ({{ u.code }})
          </option>
        </select>
      </label>
      <button v-if="unitId" class="btn" @click="generateRandom"
              title="Случайная комбинация среди разрешённых опций (std/opt)">
        Сгенерировать случайный
      </button>
      <button v-if="unitId" class="btn" @click="showSnapshot">{{ t('eaControlEmu.viewSnapshot') }}</button>
      <button v-if="unitId" class="btn" @click="showSpecification">Просмотреть спецификацию</button>
      <button v-if="unitId" class="btn" @click="showDescription">Просмотреть описание</button>
      <span v-if="error" class="error">{{ error }}</span>
    </div>

    <div v-if="pkg" class="content">
      <div class="unit-card">
        <h3>{{ pkg.unit.name }} <small>{{ pkg.unit.kind_display }}</small></h3>
      </div>

      <div v-for="section in sectionTree" :key="section.code" class="section">
        <h4>{{ section.name }}</h4>
        <template v-for="slot in slotsOf(section)" :key="slot.code">
          <div v-if="slotState(slot.code).visible && availableOptions(slot).length"
               class="slot" :class="{ blocked: slotState(slot.code).blocked }">
            <div class="slot-head">
              <strong>{{ slot.name }}</strong>
              <span class="mode">{{ slot.selection_mode }}</span>
              <span v-if="slot.required || slotState(slot.code).required" class="req">обязателен</span>
            </div>
            <div v-if="slotReadonly(slot)" class="opts readonly">
              <span class="avail">std</span>
              <span class="name">{{ availableOptions(slot)[0].name }}</span>
            </div>
            <div v-else class="opts">
              <label v-for="o in slot.options" :key="o.code"
                     :class="['opt', { na: o.availability === null, std: o.availability === 'std' }]">
                <input v-if="slot.selection_mode === 'multi'" type="checkbox"
                       :disabled="o.availability === null || slotState(slot.code).blocked"
                       :checked="(selection[slot.code] || []).includes(o.code)"
                       @change="toggleOption(slot, o)" />
                <input v-else type="radio" :name="'emu-' + slot.code"
                       :disabled="o.availability === null || slotState(slot.code).blocked"
                       :checked="selection[slot.code] === o.code"
                       @change="selection[slot.code] = o.code" />
                <span class="name">{{ o.name }}</span>
                <span v-if="o.availability" class="avail">{{ o.availability }}</span>
              </label>
            </div>
          </div>
        </template>
      </div>
    </div>

    <div v-if="view" class="modal-backdrop">
      <div class="modal">
        <div class="modal-head">
          <h3>{{ viewTitle }}</h3>
          <div class="modal-head-actions">
            <label class="lang">
              <span>{{ tLoc('eaControlEmu.language') }}</span>
              <select v-model="viewLocale">
                <option v-for="l in LOCALES" :key="l" :value="l">{{ l }}</option>
              </select>
            </label>
            <EditorActions :buttons="closeButtons" @action="onViewAction" />
          </div>
        </div>
        <div class="modal-body">
          <template v-if="view.kind === 'spec'">
            <div v-for="section in view.data.sections" :key="section.code" class="section">
              <h4>{{ section.name }} <span v-if="section.is_active === false" class="off">{{ tLoc('eaControlEmu.sectionOff') }}</span></h4>
              <table class="spec">
                <thead>
                  <tr>
                    <th>{{ tLoc('eaControlEmu.parameter') }}</th>
                    <th>{{ tLoc('eaControlEmu.value') }}</th>
                    <th>{{ tLoc('eaControlEmu.description') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="s in section.slots" :key="s.code">
                    <td class="k">{{ s.name }}</td>
                    <td>
                      <template v-if="Array.isArray(s.value)">{{ s.value.join(', ') }}</template>
                      <template v-else>{{ s.value ?? '—' }}</template>
                    </td>
                    <td class="desc">
                      <template v-if="Array.isArray(s.value_description)">{{ s.value_description.join(', ') }}</template>
                      <template v-else>{{ s.value_description ?? '—' }}</template>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
          <pre v-else-if="view.kind === 'desc'" class="desc-view">{{ view.data.text }}</pre>
          <pre v-else class="snap-view">{{ view.data.json }}</pre>
        </div>
        <div class="modal-foot">
          <EditorActions :buttons="closeButtons" @action="onViewAction" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * Эмуляция конфигуратора опций БУ (2026-11-02).
 *
 * Поток: селектор БУ → пакет (правила видимости + доступность std/opt) →
 * выбор опций (radio/checkbox по selection_mode) → «Сгенерировать случайный»
 * (случайная комбинация среди разрешённых std/opt) → просмотр спецификации/
 * описания модификации (POST /api/ea-control/specification|description/).
 * Так проверяется сценарий «поменять опцию сохранённой модификации на
 * другую разрешённую и сохранить» — серверный генератор принимает снимок
 * с произвольной валидной комбинацией и пересчитывает вывод.
 */
import { computed, onMounted, reactive, ref, watch } from 'vue'
import api from '@/shared/api'
import { DEFAULT_LOCALE, t, useI18n } from '@/shared/i18n'
import { messages } from '@/shared/i18n/locales'
import EditorActions from '@/components/EditorActions.vue'

const { locale, LOCALES } = useI18n()

const units = ref([])
const unitId = ref(null)
const pkg = ref(null)
const selection = reactive({})
const error = ref('')
// view = { kind: 'spec' | 'desc' | 'snapshot', data }
const view = ref(null)
// Локаль попапа — отдельная от глобальной: глобальная меняет ключ
// <router-view> в App.vue и перемонтирует страницу (попап бы исчез).
const viewLocale = ref(locale.value)

// Перевод подписей попапа на локаль попапа (отладка локализации).
function tLoc(key) {
  const dict = messages[viewLocale.value] || messages[DEFAULT_LOCALE]
  return dict[key] ?? messages[DEFAULT_LOCALE][key] ?? key
}

// Кнопка «Закрыть» попапа — из переиспользуемого EditorActions;
// попап закрывается только этой кнопкой (клик по фону не закрывает).
const closeButtons = computed(() => [
  { key: 'close', label: tLoc('eaControlEmu.close'), kind: 'default' },
])

const viewTitle = computed(() => {
  if (!view.value) return ''
  if (view.value.kind === 'spec') return tLoc('eaControlEmu.specTitle')
  if (view.value.kind === 'desc') return tLoc('eaControlEmu.descTitle')
  return tLoc('eaControlEmu.snapshotTitle')
})

function onViewAction(b) {
  if (b.key === 'close') view.value = null
}

// Селектор языка попапа (отладка локализации): перезапрашиваем контент
// в выбранной локали — текст попапа перерисовывается.
watch(viewLocale, () => {
  if (!view.value) return
  if (view.value.kind === 'spec' || view.value.kind === 'desc') {
    fetchView(view.value.kind)
  }
})

onMounted(async () => {
  try {
    const r = await api.get('/ea-control/units/')
    units.value = r.data || []
  } catch (e) {
    error.value = e.displayMessage || e.message || 'Не удалось загрузить список БУ'
  }
})

async function onUnitChange() {
  pkg.value = null
  view.value = null
  Object.keys(selection).forEach(k => delete selection[k])
  if (!unitId.value) return
  try {
    const r = await api.get('/ea-control/package/', {
      params: { unit: unitId.value, locale: locale.value },
    })
    pkg.value = r.data
    // значение слота control_unit для правил — код ОПЦИИ (CU_BASIC…)
    selection['control_unit'] = pkg.value.unit.option_code || pkg.value.unit.code
    applyDefaults()
  } catch (e) {
    error.value = e.displayMessage || e.message || 'Не удалось загрузить пакет'
  }
}

function applyDefaults() {
  for (const [slotCode, optionCode] of Object.entries(pkg.value?.defaults || {})) {
    if (selection[slotCode] === undefined) selection[slotCode] = optionCode
  }
  for (const slot of pkg.value?.slots || []) {
    if (selection[slot.code] !== undefined) continue
    const def = slot.options.find(o => o.is_default && o.availability !== null)
    if (def) selection[slot.code] = def.code
  }
}

function availableOptions(slot) {
  return (slot.options || []).filter(o => o.availability !== null)
}

function slotReadonly(slot) {
  const avail = availableOptions(slot)
  return avail.length === 1 && avail[0].availability === 'std'
}

function evaluate(op, expected, current) {
  if (op === 'is_set') return current !== null && current !== undefined && current !== ''
  if (op === 'not_exact') return current !== expected
  if (op === 'icontains') return String(current || '').includes(String(expected || ''))
  if (op === 'in') return Array.isArray(expected) && expected.includes(current)
  if (op === 'not_in') return Array.isArray(expected) && !expected.includes(current)
  return current === expected
}

function slotState(slotCode) {
  if (!pkg.value) return { visible: true, blocked: false, required: false }
  const value = selection['control_unit']
  const rules = pkg.value.rules.filter(r => r.target_slot === slotCode)
  const state = { visible: true, blocked: false, required: false }
  for (const r of [...rules].sort((a, b) => (a.priority - b.priority) || (a.id - b.id))) {
    const current = r.when_slot === 'control_unit' ? value : selection[r.when_slot]
    if (!evaluate(r.operator, r.when_value, current)) continue
    if (r.action === 'show') state.visible = true
    else if (r.action === 'hide') state.visible = false
    else if (r.action === 'block') state.blocked = true
    else if (r.action === 'require') state.required = true
  }
  return state
}

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

const snapshotJson = computed(() =>
  JSON.stringify(snapshotObject(), null, 2))

function snapshotObject() {
  const out = {}
  for (const slot of pkg.value?.slots || []) {
    if (selection[slot.code] !== undefined && selection[slot.code] !== null) {
      out[slot.code] = selection[slot.code]
    }
  }
  return out
}

function toggleOption(slot, o) {
  const arr = selection[slot.code] ? [...selection[slot.code]] : []
  const i = arr.indexOf(o.code)
  if (i >= 0) arr.splice(i, 1)
  else arr.push(o.code)
  selection[slot.code] = arr
}

/** Случайная комбинация: для каждого видимого слота — случайная опция
 *  среди разрешённых (std/opt). */
function generateRandom() {
  if (!pkg.value) return
  for (const slot of pkg.value.slots) {
    if (!slotState(slot.code).visible) continue
    const avail = availableOptions(slot)
    if (!avail.length) continue
    if (slot.selection_mode === 'multi') {
      selection[slot.code] = avail
        .filter(o => Math.random() < 0.5)
        .map(o => o.code)
    } else {
      const o = avail[Math.floor(Math.random() * avail.length)]
      selection[slot.code] = o.code
    }
  }
}

async function showSpecification() {
  viewLocale.value = locale.value
  await fetchView('spec')
}

async function showDescription() {
  viewLocale.value = locale.value
  await fetchView('desc')
}

function showSnapshot() {
  viewLocale.value = locale.value
  view.value = { kind: 'snapshot', data: { json: snapshotJson.value } }
}

async function fetchView(kind) {
  const url = kind === 'spec' ? '/ea-control/specification/' : '/ea-control/description/'
  try {
    const r = await api.post(url, {
      unit: unitId.value,
      snapshot: snapshotObject(),
      // выбранная схема цепей (CMD_WIRING) перерезолвивает набор сигналов
      // CMD_*: строки матрицы с координатой signal_power
      signal_power: wiringSignalPowerId(),
      locale: viewLocale.value,
    })
    view.value = kind === 'spec'
      ? { kind, data: r.data }
      : { kind, data: { text: r.data.text } }
  } catch (e) {
    error.value = e.displayMessage || e.message || 'Не удалось сгенерировать'
  }
}

function wiringSignalPowerId() {
  const slot = (pkg.value?.slots || []).find(s => s.code === 'CMD_WIRING')
  if (!slot) return null
  const o = (slot.options || []).find(x => x.code === selection['CMD_WIRING'])
  return o?.signal_power_id || null
}
</script>

<style scoped>
.cu-emu { font-family: -apple-system, 'Segoe UI', Roboto, sans-serif; max-width: 860px; }
.hint { color: #666; margin: 0 0 10px; }
.selects { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin-bottom: 14px; }
.selects label { display: flex; gap: 6px; align-items: center; }
.btn { border: 1px solid #bbb; background: #fff; border-radius: 4px; padding: 4px 10px; cursor: pointer; }
.btn:hover { background: #f2f6ff; }
.error { color: #b00; }
.unit-card h3 { margin: 0 0 4px; }
.unit-card small { color: #888; font-weight: normal; }
.section { margin: 10px 0; border-left: 3px solid #e3e8f0; padding-left: 10px; }
.section h4 { margin: 4px 0; }
.slot { display: flex; align-items: flex-start; gap: 12px; margin: 4px 0; }
.slot-head { flex: 0 0 250px; min-width: 0; display: flex; gap: 8px; align-items: center; }
.slot-head .mode, .slot-head .req { font-size: 11px; color: #888; border: 1px solid #ddd; border-radius: 3px; padding: 0 4px; }
.slot-head .req { color: #a40; border-color: #ecb; }
.opts { flex: 1; display: flex; flex-wrap: wrap; gap: 6px 14px; }
.opts.readonly { display: flex; gap: 8px; }
.opt { display: flex; gap: 5px; align-items: center; }
.opt.na { opacity: .45; }
.opt.std .name { font-weight: 600; }
.avail { font-size: 11px; color: #888; }
/* Попап спецификации/описания: закрывается только кнопкой «Закрыть»
   (у .modal-backdrop нет обработчика клика). */
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0, 0, 0, .45);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.modal { background: #fff; border-radius: 6px; padding: 16px; width: min(960px, 92vw); max-height: 88vh; display: flex; flex-direction: column; }
.modal-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.modal-head h3 { margin: 0; }
.modal-head-actions { display: flex; align-items: center; gap: 14px; }
.modal-head-actions .lang { display: flex; align-items: center; gap: 6px; color: #444; font-size: 13px; }
.modal-head-actions .lang select { padding: 2px 4px; border: 1px solid #ccc; border-radius: 3px; }
.modal-body { overflow: auto; flex: 1; }
.modal-foot { display: flex; justify-content: flex-end; margin-top: 12px; }
.off { color: #a66; font-weight: normal; font-size: 12px; }
table.spec { border-collapse: collapse; font-size: 13px; width: 100%; }
table.spec th, table.spec td { border: 1px solid #e0e7e0; padding: 3px 8px; vertical-align: top; text-align: left; }
table.spec th { background: #f2f6f2; }
table.spec td.k { width: 32%; font-weight: 600; }
table.spec td.desc { color: #555; width: 40%; }
.desc-view { white-space: pre-wrap; background: #fff; border: 1px solid #e3e8f0; padding: 10px; margin: 0; }
.snap-view { white-space: pre-wrap; background: #f6f8fa; border: 1px solid #e3e8f0; padding: 8px; margin: 0; font-family: ui-monospace, Consolas, monospace; }
</style>
