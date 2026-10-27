<template>
  <div class="structure-page">
    <!-- ЛЕВАЯ ЧАСТЬ: выбор узла -->
    <div class="left-pane">
      <div class="pane-head">
        <h3>Узлы</h3>
        <EditorActions align="start"
                       :buttons="[{ key: 'add', label: t('eaControl.addNode'), kind: 'primary' }]"
                       @action="onNodeAction" />
      </div>
      <div class="node-list">
        <div v-for="n in sectionTree" :key="n.id" class="node-item"
             :class="{ active: draft.node && draft.node.id === n.id }"
             :style="{ paddingLeft: (n.depth * 14) + 'px' }"
             @click="onNodeClick(n)">
          <span class="label">{{ n.name || n.code }}</span>
          <span class="code">{{ n.code }}</span>
        </div>
        <div class="node-item new" :class="{ active: draft.node && draft.node.id == null }"
             @click="onAddNode">
          <span class="label">+ Новый узел</span>
        </div>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
    </div>

    <!-- ПРАВАЯ ЧАСТЬ: редакторы -->
    <div class="right-pane">
      <div v-if="!draft.node" class="empty">Выберите узел слева.</div>

      <div v-else class="editors">
        <div v-if="error" class="save-error">{{ error }}</div>
        <div v-if="success" class="save-ok">{{ success }}</div>
        <!-- УЗЕЛ -->
        <div class="editor">
          <div class="editor-head">
            <span class="entity-label">Узел:</span>
            <input class="entity-name" v-model="draft.node.name" placeholder="Название узла"
                   @input="markDirty('node')" />
            <span v-if="hasChanges" class="dirty">не сохранено</span>
            <EditorActions :buttons="nodeButtons" @action="onNodeAction" />
          </div>
          <div v-if="draft.node._deleted" class="del-banner">Узел будет удалён при сохранении.</div>

          <div class="form" @input="markDirty('node')" @change="markDirty('node')">
            <div class="form-row">
              <label class="form-field"><span>Код</span><input v-model="draft.node.code" /></label>
              <label class="form-field"><span>Родитель</span>
                <select v-model="draft.node.parent">
                  <option :value="null">— корневой —</option>
                  <option v-for="o in parentOptions" :key="o.id" :value="o.id">{{ o.label }}</option>
                </select>
              </label>
            </div>
            <div class="form-row">
              <label class="form-field"><span>Описание</span><textarea v-model="draft.node.description" rows="2"></textarea></label>
            </div>
            <div class="form-row">
              <label class="form-field"><span>Сортировка</span><input type="number" v-model.number="draft.node.sorting_order" /></label>
              <label class="form-field chk"><span>Активно</span><input type="checkbox" v-model="draft.node.is_active" /></label>
            </div>
          </div>

          <!-- СЛОТЫ (чипсы) -->
          <div class="sub-head">
            <h4>Слоты узла «{{ nodeName }}»</h4>
            <EditorActions align="start"
                           :buttons="[{ key: 'add', label: t('eaControl.addSlot'), kind: 'primary' }]"
                           @action="onSlotAction" />
          </div>
          <div class="chips">
            <div v-for="(sl, i) in draft.slots" :key="i" class="chip"
                 :class="{ active: selSlotIdx === i, deleted: sl._deleted }"
                 @click="selectSlotAt(i)">
              {{ sl.name || sl.code || 'новый слот' }}
              <span v-if="sl._deleted" class="del-mark">×</span>
            </div>
            <div v-if="!draft.slots.length" class="hint">Слотов нет — добавьте первый.</div>
          </div>

          <!-- СЛОТ -->
          <div v-if="selSlot" class="editor nested">
            <div class="editor-head">
              <span class="entity-label">Слот:</span>
              <input class="entity-name" v-model="selSlot.name" placeholder="Название слота"
                     @input="markDirty('slot')" />
              <EditorActions :buttons="slotButtons" @action="onSlotAction" />
            </div>
            <div v-if="selSlot._deleted" class="del-banner">Слот будет удалён при сохранении.</div>

            <div class="form" @input="markDirty('slot')" @change="markDirty('slot')">
              <div class="form-row">
                <label class="form-field"><span>Код</span><input v-model="selSlot.code" /></label>
                <label class="form-field"><span>Раздел</span>
                  <div class="section-picker">
                    <button type="button" class="sp-btn" @click="toggleSectionMenu">
                      <span class="sp-val">{{ sectionLabel(selSlot.section) }}</span>
                      <span class="sp-caret">▾</span>
                    </button>
                    <div v-if="sectionOpen" class="sp-menu">
                      <div class="sp-item" :class="{ active: selSlot.section == null }"
                           @mousedown.prevent="pickSection(null)">— без раздела —</div>
                      <div v-for="o in sectionTree" :key="o.id" class="sp-item"
                           :class="{ active: selSlot.section === o.id }"
                           :style="{ paddingLeft: (o.depth * 14 + 10) + 'px' }"
                           @mousedown.prevent="pickSection(o.id)">{{ o.name || o.code }}</div>
                    </div>
                  </div>
                </label>
              </div>
              <div class="form-row">
                <label class="form-field chk"><span>Обязательный</span><input type="checkbox" v-model="selSlot.required" /></label>
              </div>
              <div class="form-row">
                <label class="form-field"><span>Режим выбора</span>
                  <select v-model="selSlot.selection_mode">
                    <option value="single">Одиночный</option>
                    <option value="multi">Мульти</option>
                    <option value="xor">Взаимоисключающий</option>
                    <option value="bundle">Пакет</option>
                  </select>
                </label>
                <label class="form-field"><span>Род значения</span>
                  <select v-model="selSlot.slot_kind">
                    <option value="value">Значение</option>
                    <option value="object">Объект</option>
                    <option value="subtype">Подтип</option>
                  </select>
                </label>
              </div>
              <div class="form-row">
                <label class="form-field"><span>Описание</span><textarea v-model="selSlot.description" rows="2"></textarea></label>
              </div>
              <div class="form-row">
                <label class="form-field"><span>Сортировка</span><input type="number" v-model.number="selSlot.sorting_order" /></label>
                <label class="form-field chk"><span>Активно</span><input type="checkbox" v-model="selSlot.is_active" /></label>
              </div>
            </div>

            <!-- ОПЦИИ (чипсы) -->
            <div class="sub-head">
              <h4>Опции слота «{{ slotName }}»</h4>
              <EditorActions align="start"
                             :buttons="[{ key: 'add', label: t('eaControl.addOption'), kind: 'primary' }]"
                             @action="onOptionAction" />
            </div>
            <div class="chips">
              <div v-for="(op, i) in (selSlot.options || [])" :key="i" class="chip"
                   :class="{ active: selOptionIdx === i, deleted: op._deleted }"
                   @click="selectOptionAt(i)">
                {{ op.name || op.code || 'новая опция' }}
                <span v-if="op._deleted" class="del-mark">×</span>
              </div>
              <div v-if="!(selSlot.options || []).length" class="hint">Опций нет — добавьте первую.</div>
            </div>

            <!-- ОПЦИЯ -->
            <div v-if="selOption" class="editor nested">
              <div class="editor-head">
                <span class="entity-label">Опция:</span>
                <input class="entity-name" v-model="selOption.name" placeholder="Название опции"
                       @input="markDirty('option')" />
                <EditorActions :buttons="optionButtons" @action="onOptionAction" />
              </div>
              <div v-if="selOption._deleted" class="del-banner">Опция будет удалена при сохранении.</div>

              <div class="form" @input="markDirty('option')" @change="markDirty('option')">
                <div class="form-row">
                  <label class="form-field"><span>Код</span><input v-model="selOption.code" /></label>
                  <label class="form-field"><span>Тип опции</span>
                    <select v-model="selOption.kind" @change="resetOptionPayload">
                      <option value="signal">Сигнал</option>
                      <option value="heater">Обогрев</option>
                      <option value="power">Питание цепей</option>
                      <option value="logic">Логика</option>
                      <option value="unit">БУ</option>
                      <option value="local_control">Орган управления</option>
                      <option value="display">Вид отображения</option>
                      <option value="unit_power">Питание БУ</option>
                      <option value="cable_gland">Кабельные вводы</option>
                      <option value="none">None-строка</option>
                      <option value="pair">Пара контактов</option>
                    </select>
                  </label>
                </div>

                <template v-if="selOption.kind === 'signal'">
                  <div class="form-row">
                    <label class="form-field"><span>Командный</span>
                      <select v-model="selOption.control_signal">
                        <option :value="null">— —</option>
                        <option v-for="o in dicts.controlSignals" :key="o.id" :value="o.id">{{ o.label }}</option>
                      </select>
                    </label>
                    <label class="form-field"><span>Сигнал ОС</span>
                      <select v-model="selOption.feedback_signal">
                        <option :value="null">— —</option>
                        <option v-for="o in dicts.feedbackSignals" :key="o.id" :value="o.id">{{ o.label }}</option>
                      </select>
                    </label>
                  </div>
                  <div class="form-row">
                    <label class="form-field"><span>Протокол</span>
                      <select v-model="selOption.protocol">
                        <option :value="null">— —</option>
                        <option v-for="o in dicts.protocols" :key="o.id" :value="o.id">{{ o.label }}</option>
                      </select>
                    </label>
                    <label class="form-field"><span>Устройство</span>
                      <select v-model="selOption.device">
                        <option :value="null">— —</option>
                        <option v-for="o in dicts.devices" :key="o.id" :value="o.id">{{ o.label }}</option>
                      </select>
                    </label>
                  </div>
                </template>
                <div v-else-if="selOption.kind === 'heater'" class="form-row">
                  <label class="form-field"><span>Обогрев</span>
                    <select v-model="selOption.heater_supply">
                      <option :value="null">— —</option>
                      <option v-for="o in dicts.heaterSupplies" :key="o.id" :value="o.id">{{ o.label }}</option>
                    </select>
                  </label>
                </div>
                <div v-else-if="selOption.kind === 'power'" class="form-row">
                  <label class="form-field"><span>Питание цепей</span>
                    <select v-model="selOption.signal_power">
                      <option :value="null">— —</option>
                      <option v-for="o in dicts.signalPowers" :key="o.id" :value="o.id">{{ o.label }}</option>
                    </select>
                  </label>
                </div>
                <div v-else-if="selOption.kind === 'logic'" class="form-row">
                  <label class="form-field"><span>Логика</span>
                    <select v-model="selOption.control_logic">
                      <option :value="null">— —</option>
                      <option v-for="o in dicts.controlLogics" :key="o.id" :value="o.id">{{ o.label }}</option>
                    </select>
                  </label>
                </div>
                <div v-else-if="selOption.kind === 'unit'" class="form-row">
                  <label class="form-field"><span>Блок управления</span>
                    <select v-model="selOption.control_unit">
                      <option :value="null">— —</option>
                      <option v-for="o in dicts.units" :key="o.id" :value="o.id">{{ o.label }}</option>
                    </select>
                  </label>
                </div>
                <div v-else-if="selOption.kind === 'local_control'" class="form-row">
                  <label class="form-field"><span>Орган управления</span>
                    <select v-model="selOption.local_control_type">
                      <option :value="null">— —</option>
                      <option v-for="o in dicts.localControlTypes" :key="o.id" :value="o.id">{{ o.label }}</option>
                    </select>
                  </label>
                </div>
                <div v-else-if="selOption.kind === 'display'" class="form-row">
                  <div class="form-field">
                    <span>Виды отображения</span>
                    <div class="ms">
                      <label v-for="o in dicts.displayTypes" :key="o.id" class="ms-item">
                        <input type="checkbox" :value="o.id"
                               :checked="(selOption.display_types || []).includes(o.id)"
                               @change="toggleOptionMs('display_types', o.id)" />
                        {{ o.label }}
                      </label>
                    </div>
                  </div>
                </div>
                <div v-else-if="selOption.kind === 'unit_power'" class="form-row">
                  <label class="form-field"><span>Питание БУ</span>
                    <select v-model="selOption.unit_power_source">
                      <option :value="null">— —</option>
                      <option v-for="o in dicts.unitPowerSources" :key="o.id" :value="o.id">{{ o.label }}</option>
                    </select>
                  </label>
                </div>
                <div v-else-if="selOption.kind === 'cable_gland'" class="form-row">
                  <label class="form-field"><span>Набор резьб вводов</span>
                    <select v-model="selOption.cable_gland_set">
                      <option :value="null">— —</option>
                      <option v-for="o in dicts.threadSets" :key="o.id" :value="o.id">{{ o.label }}</option>
                    </select>
                  </label>
                </div>

                <div class="form-row">
                  <label class="form-field"><span>Кодировка</span><input v-model="selOption.encoding" /></label>
                  <label class="form-field"><span>Ext-код</span><input v-model="selOption.ext_encoding" /></label>
                </div>
                <div class="form-row">
                  <label class="form-field"><span>Описание</span><textarea v-model="selOption.description" rows="2"></textarea></label>
                </div>
                <div class="form-row">
                  <label class="form-field"><span>Сортировка</span><input type="number" v-model.number="selOption.sorting_order" /></label>
                  <label class="form-field chk"><span>Активно</span><input type="checkbox" v-model="selOption.is_active" /></label>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * Конфигуратор опций БУ — полноэкранный редактор структуры
 * «узел → слоты → опции» (slots.md, роли Node/Slot/Option).
 *
 * Редактирование идёт в локальном черновике (draft); в БД ничего не пишется
 * до кнопки «Сохранить». «Сохранить» коммитит топологически: узел → слоты →
 * опции (новые — POST, изменённые — PUT, помеченные «удалить» — DELETE).
 * Удаление двухшаговое: пометка `_deleted` обратима до сохранения.
 */
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import api from '@/shared/api'
import { t } from '@/shared/i18n'
import EditorActions from '@/components/EditorActions.vue'

const loading = ref(false)
const error = ref('')
const success = ref('')
const sections = ref([])
const slots = ref([])
const options = ref([])
const dicts = reactive({
  controlSignals: [], feedbackSignals: [], protocols: [], devices: [],
  heaterSupplies: [], signalPowers: [], controlLogics: [],
  units: [], localControlTypes: [], displayTypes: [], unitPowerSources: [],
  threadSets: [],
})

// Черновик выбранного узла: { node, slots: [ { ..., options: [...] } ] }
const draft = reactive({ node: null, slots: [] })
const selSlotIdx = ref(-1)
const selOptionIdx = ref(-1)
const dirty = reactive({ node: false, slot: false, option: false })

const selSlot = computed(() => draft.slots[selSlotIdx.value] || null)
const selOption = computed(() => {
  const s = selSlot.value
  return (s && s.options && s.options[selOptionIdx.value]) || null
})

const nodeName = computed(() =>
  (draft.node && (draft.node.name || draft.node.code)) || 'новый')
const slotName = computed(() =>
  (selSlot.value && (selSlot.value.name || selSlot.value.code)) || 'новый')

const nodeDeleteLabel = computed(() =>
  (draft.node && draft.node.id == null) ? t('eaControl.cancelCreate') : t('eaControl.deleteNode'))

// Кнопки редакторов через общий EditorActions (label уже локализованы)
const nodeButtons = computed(() => [
  { key: 'save', label: t('eaControl.save'), kind: 'primary', disabled: !hasChanges.value },
  { key: 'delete',
    label: (draft.node && draft.node._deleted) ? t('eaControl.cancelDelete') : nodeDeleteLabel.value,
    kind: (draft.node && draft.node._deleted) ? 'danger' : 'default' },
])

const slotButtons = computed(() => [
  { key: 'copy', label: 'Копировать', kind: 'default' },
  { key: 'save', label: t('eaControl.save'), kind: 'primary', disabled: !hasSlotChanges.value },
  { key: 'delete',
    label: (selSlot.value && selSlot.value._deleted) ? t('eaControl.cancelDelete') : t('eaControl.deleteSlot'),
    kind: (selSlot.value && selSlot.value._deleted) ? 'danger' : 'default' },
])

const optionButtons = computed(() => [
  { key: 'delete',
    label: (selOption.value && selOption.value._deleted) ? t('eaControl.cancelDelete') : t('eaControl.deleteOption'),
    kind: (selOption.value && selOption.value._deleted) ? 'danger' : 'default' },
])

function onNodeAction(b) {
  if (b.key === 'save') commitAll()
  else if (b.key === 'delete') toggleDeleteNode()
  else if (b.key === 'add') onAddNode()
}

function onSlotAction(b) {
  if (b.key === 'save') commitSlot()
  else if (b.key === 'copy') copySlot()
  else if (b.key === 'delete') toggleDeleteSlot()
  else if (b.key === 'add') addSlot()
}

function onOptionAction(b) {
  if (b.key === 'delete') toggleDeleteOption()
  else if (b.key === 'add') addOption()
}

const sectionTree = computed(() => {
  const byParent = {}
  for (const s of sections.value) {
    const key = s.parent || 0
    if (!byParent[key]) byParent[key] = []
    byParent[key].push(s)
  }
  const out = []
  const seen = new Set()
  const walk = (parentId, depth) => {
    const kids = (byParent[parentId] || []).slice()
      .sort((a, b) => a.sorting_order - b.sorting_order)
    for (const s of kids) {
      if (seen.has(s.id)) continue
      seen.add(s.id)
      out.push({ ...s, depth })
      walk(s.id, depth + 1)
    }
  }
  walk(0, 0)
  return out
})

const parentOptions = computed(() => {
  const excluded = new Set()
  if (draft.node && draft.node.id != null) {
    excluded.add(draft.node.id)
    const children = {}
    for (const s of sections.value) {
      if (s.parent) {
        if (!children[s.parent]) children[s.parent] = []
        children[s.parent].push(s.id)
      }
    }
    const stack = [draft.node.id]
    while (stack.length) {
      const id = stack.pop()
      for (const c of (children[id] || [])) {
        if (!excluded.has(c)) {
          excluded.add(c)
          stack.push(c)
        }
      }
    }
  }
  return sections.value
    .filter(s => !excluded.has(s.id))
    .map(s => ({ id: s.id, label: s.name || s.code }))
})

// ── Селектор «Раздел»: свой dropdown вместо нативного select ────────────
// Нативный popup в Chrome периодически закрывается, не закоммитив выбор
// (change приходит со СТАРЫМ значением), поэтому выбор раздела сделан
// детерминированным списком на mousedown.prevent.
const sectionOpen = ref(false)

function sectionLabel(id) {
  if (id == null) return '— без раздела —'
  const s = sections.value.find(x => x.id === id)
  return (s && (s.name || s.code)) || ('#' + id)
}

function toggleSectionMenu() {
  sectionOpen.value = !sectionOpen.value
}

function pickSection(id) {
  const s = selSlot.value
  if (s) {
    s.section = id
    markDirty('slot')
  }
  sectionOpen.value = false
}

function onDocClick(e) {
  if (!(e.target && e.target.closest && e.target.closest('.section-picker'))) {
    sectionOpen.value = false
  }
}

const hasPendingDeletes = computed(() => {
  if (draft.node && draft.node._deleted) return true
  return draft.slots.some(s => s._deleted || (s.options || []).some(o => o._deleted))
})

const hasChanges = computed(() =>
  dirty.node || dirty.slot || dirty.option || hasPendingDeletes.value)

const hasSlotChanges = computed(() =>
  dirty.slot || dirty.option
  || (selSlot.value && selSlot.value._deleted)
  || (selSlot.value && (selSlot.value.options || []).some(o => o._deleted)))

function markDirty(kind) {
  dirty[kind] = true
}

onMounted(() => document.addEventListener('click', onDocClick))
onUnmounted(() => document.removeEventListener('click', onDocClick))

function dictList(rows) {
  return rows.map(o => ({ id: o.id, label: o.name || o.code || String(o.id) }))
}

async function reload() {
  loading.value = true
  error.value = ''
  try {
    const [s, sl, o, units, ctl, fb, proto, dev, heater, power, logic,
      lct, dsp, upw, meta] =
      await Promise.all([
        api.get('/ea-control/sections/'),
        api.get('/ea-control/slots/'),
        api.get('/ea-control/slot-options/'),
        api.get('/ea-control/units/'),
        api.get('/ea-control/control-signals/'),
        api.get('/ea-control/feedback-signals/'),
        api.get('/ea-control/comm-protocols/'),
        api.get('/ea-control/feedback-devices/'),
        api.get('/ea-control/heater-supplies/'),
        api.get('/ea-control/signal-powers/'),
        api.get('/ea-control/control-logics/'),
        api.get('/ea-control/local-control-types/'),
        api.get('/ea-control/display-types/'),
        api.get('/ea-control/unit-power-sources/'),
        api.get('/ea-control/meta/'),
      ])
    sections.value = s.data.results || s.data || []
    slots.value = sl.data.results || sl.data || []
    options.value = o.data.results || o.data || []
    dicts.units = dictList(units.data)
    dicts.controlSignals = dictList(ctl.data.results || ctl.data || [])
    dicts.feedbackSignals = dictList(fb.data.results || fb.data || [])
    dicts.protocols = dictList(proto.data.results || proto.data || [])
    dicts.devices = dictList(dev.data.results || dev.data || [])
    dicts.heaterSupplies = dictList(heater.data.results || heater.data || [])
    dicts.signalPowers = dictList(power.data.results || power.data || [])
    dicts.controlLogics = dictList(logic.data.results || logic.data || [])
    dicts.localControlTypes = dictList(lct.data.results || lct.data || [])
    dicts.displayTypes = dictList(dsp.data.results || dsp.data || [])
    dicts.unitPowerSources = dictList(upw.data.results || upw.data || [])
    dicts.threadSets = dictList(meta.data.thread_sets || [])
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка загрузки'
  } finally {
    loading.value = false
  }
}

// ── Черновик ──────────────────────────────────────────────────────────────

function cloneOption(o) {
  return {
    id: o.id, code: o.code, name: o.name, slot: o.slot, kind: o.kind,
    control_signal: o.control_signal, feedback_signal: o.feedback_signal,
    protocol: o.protocol, heater_supply: o.heater_supply,
    signal_power: o.signal_power, control_logic: o.control_logic,
    control_unit: null, device: null,
    local_control_type: o.local_control_type,
    display_types: [...(o.display_types || [])],
    unit_power_source: o.unit_power_source,
    cable_gland_set: o.cable_gland_set,
    encoding: o.encoding || '', ext_encoding: o.ext_encoding || '',
    description: o.description || '', sorting_order: o.sorting_order || 0,
    is_active: o.is_active,
  }
}

function cloneSlot(s) {
  return {
    id: s.id, code: s.code, name: s.name, section: s.section,
    selection_mode: s.selection_mode, slot_kind: s.slot_kind,
    required: s.required, description: s.description || '',
    sorting_order: s.sorting_order || 0, is_active: s.is_active,
    options: options.value
      .filter(o => o.slot === s.id)
      .sort((a, b) => a.sorting_order - b.sorting_order)
      .map(cloneOption),
  }
}

function onNodeClick(n) {
  if (hasChanges.value && !confirm('Есть несохранённые изменения. Отменить их и переключиться?')) return
  selectNode(n)
}

function onAddNode() {
  if (hasChanges.value && !confirm('Есть несохранённые изменения. Отменить их?')) return
  addNode()
}

function selectNode(n) {
  draft.node = {
    id: n.id, code: n.code, name: n.name, parent: n.parent,
    description: n.description || '', sorting_order: n.sorting_order || 0,
    is_active: n.is_active,
  }
  draft.slots = slots.value
    .filter(s => s.section === n.id)
    .sort((a, b) => a.sorting_order - b.sorting_order)
    .map(cloneSlot)
  selSlotIdx.value = -1
  selOptionIdx.value = -1
  dirty.node = dirty.slot = dirty.option = false
}

function addNode() {
  draft.node = {
    id: null, code: '', name: '', parent: null, description: '',
    sorting_order: 0, is_active: true,
  }
  draft.slots = []
  selSlotIdx.value = -1
  selOptionIdx.value = -1
  dirty.node = dirty.slot = dirty.option = false
  dirty.node = true
}

function selectSlotAt(i) {
  selSlotIdx.value = i
  selOptionIdx.value = -1
}

function addSlot() {
  const maxOrder = draft.slots.reduce((m, s) => Math.max(m, s.sorting_order || 0), -1)
  draft.slots.push({
    id: null, code: '', name: '', section: draft.node ? draft.node.id : null, selection_mode: 'single',
    slot_kind: 'value', required: false, description: '',
    sorting_order: maxOrder + 1, is_active: true, options: [],
  })
  selSlotIdx.value = draft.slots.length - 1
  selOptionIdx.value = -1
  dirty.slot = true
}

function selectOptionAt(i) {
  selOptionIdx.value = i
}

function addOption() {
  const s = selSlot.value
  if (!s) return
  s.options = s.options || []
  const maxOrder = s.options.reduce((m, o) => Math.max(m, o.sorting_order || 0), -1)
  s.options.push({
    id: null, code: '', name: '', slot: null, kind: 'signal',
    control_signal: null, feedback_signal: null, protocol: null,
    heater_supply: null, signal_power: null, control_logic: null,
    control_unit: null, device: null,
    local_control_type: null, display_types: [],
    unit_power_source: null, cable_gland_set: null,
    encoding: '', ext_encoding: '', description: '',
    sorting_order: maxOrder + 1, is_active: true,
  })
  selOptionIdx.value = s.options.length - 1
  dirty.option = true
}

function resetOptionPayload() {
  const o = selOption.value
  if (!o) return
  o.control_signal = null
  o.feedback_signal = null
  o.protocol = null
  o.heater_supply = null
  o.signal_power = null
  o.control_logic = null
  o.control_unit = null
  o.device = null
  o.local_control_type = null
  o.display_types = []
  o.unit_power_source = null
  o.cable_gland_set = null
}

function toggleOptionMs(name, id) {
  const o = selOption.value
  if (!o) return
  const arr = o[name] || []
  const i = arr.indexOf(id)
  if (i >= 0) arr.splice(i, 1)
  else arr.push(id)
  o[name] = arr
}

function toggleDeleteNode() {
  if (draft.node.id == null) {
    // новый (несохранённый) узел — сразу отменяем создание
    draft.node = null
    draft.slots = []
    selSlotIdx.value = -1
    selOptionIdx.value = -1
    dirty.node = dirty.slot = dirty.option = false
    return
  }
  draft.node._deleted = !draft.node._deleted
}

function toggleDeleteSlot() {
  const s = selSlot.value
  if (s) s._deleted = !s._deleted
}

function toggleDeleteOption() {
  const o = selOption.value
  if (o) o._deleted = !o._deleted
}

// ── Сохранение ────────────────────────────────────────────────────────────

function cleanNode(n) {
  const p = {}
  for (const k of Object.keys(n)) {
    if (k === 'id' || k === '_deleted') continue
    p[k] = n[k]
  }
  if (p.sorting_order == null || p.sorting_order === '') p.sorting_order = 0
  return p
}

function cleanSlot(s) {
  const p = {}
  for (const k of Object.keys(s)) {
    if (k === 'id' || k === '_deleted' || k === 'options') continue
    p[k] = s[k]
  }
  if (p.sorting_order == null || p.sorting_order === '') p.sorting_order = 0
  return p
}

function cleanOption(o) {
  const p = {}
  for (const k of Object.keys(o)) {
    if (k === 'id' || k === '_deleted') continue
    p[k] = o[k]
  }
  if (p.sorting_order == null || p.sorting_order === '') p.sorting_order = 0
  return p
}

function validateSlotDraft(slot, seenSlotCodes) {
  const errs = []
  const slotLabel = slot.name || slot.code || 'новый слот'
  if (!slot.code || !slot.code.trim()) {
    errs.push(`слот «${slotLabel}»: код`)
  } else {
    const code = slot.code.trim()
    if (seenSlotCodes.has(code)) {
      errs.push(`слот «${slotLabel}»: код «${code}» повторяется в этом узле`)
    }
    seenSlotCodes.add(code)
    if (slots.value.some(s => s.code === code && s.id !== slot.id)) {
      errs.push(`слот «${slotLabel}»: код «${code}» уже занят другим слотом`)
    }
  }
  const seenOptCodes = new Set()
  for (const opt of (slot.options || [])) {
    if (opt._deleted) continue
    const optLabel = opt.name || opt.code || 'новая опция'
    if (!opt.code || !opt.code.trim()) {
      errs.push(`опция в слоте «${slotLabel}»: код`)
      continue
    }
    const ocode = opt.code.trim()
    if (seenOptCodes.has(ocode)) {
      errs.push(`опция в слоте «${slotLabel}»: код «${ocode}» повторяется`)
    }
    seenOptCodes.add(ocode)
    if (options.value.some(o => o.code === ocode && o.id !== opt.id)) {
      errs.push(`опция в слоте «${slotLabel}»: код «${ocode}» уже занят другой опцией`)
    }
    if ((opt.kind === 'none' || opt.kind === 'pair') && (!opt.name || !opt.name.trim())) {
      errs.push(`опция в слоте «${slotLabel}»: название (обязательно для none/pair)`)
    }
    if (opt.kind === 'display' && !(opt.display_types || []).length) {
      errs.push(`опция в слоте «${slotLabel}»: вид отображения`)
    }
    if (opt.kind === 'unit_power' && !opt.unit_power_source) {
      errs.push(`опция в слоте «${slotLabel}»: питание БУ`)
    }
    if (opt.kind === 'power' && !opt.signal_power) {
      errs.push(`опция в слоте «${slotLabel}»: схема цепей управления`)
    }
    if (opt.kind === 'logic' && !opt.control_logic) {
      errs.push(`опция в слоте «${slotLabel}»: логика работы`)
    }
    if (opt.kind === 'cable_gland' && !opt.cable_gland_set) {
      errs.push(`опция в слоте «${slotLabel}»: набор резьб вводов`)
    }
  }
  return errs
}

function validateDraft() {
  const errs = []
  if (!draft.node.code || !draft.node.code.trim()) errs.push('узел: код')
  else if (sections.value.some(s => s.code === draft.node.code.trim()
      && s.id !== draft.node.id)) {
    errs.push(`узел: код «${draft.node.code.trim()}» уже занят другим узлом`)
  }
  if (!draft.node.name || !draft.node.name.trim()) errs.push('узел: название')
  const seenSlotCodes = new Set()
  for (const slot of draft.slots) {
    if (slot._deleted) continue
    errs.push(...validateSlotDraft(slot, seenSlotCodes))
  }
  return errs
}

let successTimer = null
function flashSuccess(msg) {
  success.value = msg
  if (successTimer) clearTimeout(successTimer)
  successTimer = setTimeout(() => { success.value = '' }, 2500)
}

async function persistSlot(slot, fallbackSection) {
  if (slot._deleted) {
    if (slot.id != null) await api.delete(`/ea-control/slots/${slot.id}/`)
    return null
  }
  let slotId = slot.id
  if (slotId == null) {
    const section = (slot.section == null && fallbackSection != null) ? fallbackSection : slot.section
    const r = await api.post('/ea-control/slots/', { ...cleanSlot(slot), section })
    slotId = r.data.id
    slot.id = slotId
  } else {
    await api.put(`/ea-control/slots/${slotId}/`, cleanSlot(slot))
  }
  return slotId
}

async function persistSlotOptions(slot, slotId) {
  for (const opt of (slot.options || [])) {
    if (opt._deleted) {
      if (opt.id != null) await api.delete(`/ea-control/slot-options/${opt.id}/`)
      continue
    }
    if (opt.id == null) {
      const r = await api.post('/ea-control/slot-options/',
        { ...cleanOption(opt), slot: slotId })
      opt.id = r.data.id
    } else {
      await api.put(`/ea-control/slot-options/${opt.id}/`, cleanOption(opt))
    }
  }
}

// Перечитать слоты текущего узла после сохранения одного слота,
// не трогая черновик узла и его флаг dirty.node.
function refreshSlotDraft() {
  const nodeId = draft.node ? draft.node.id : null
  draft.slots = slots.value
    .filter(s => s.section === nodeId)
    .sort((a, b) => a.sorting_order - b.sorting_order)
    .map(cloneSlot)
  selSlotIdx.value = -1
  selOptionIdx.value = -1
  dirty.slot = dirty.option = false
}

async function commitAll() {
  error.value = ''
  const errs = validateDraft()
  if (errs.length) {
    error.value = 'Заполните обязательные поля: ' + errs.join('; ')
    return
  }
  try {
    // 1. Узел
    if (draft.node._deleted) {
      if (draft.node.id != null) await api.delete(`/ea-control/sections/${draft.node.id}/`)
      draft.node = null
      draft.slots = []
      selSlotIdx.value = -1
      selOptionIdx.value = -1
      dirty.node = dirty.slot = dirty.option = false
      await reload()
      flashSuccess('Узел удалён')
      return
    }
    const nodeWasNew = draft.node.id == null
    let nodeId = draft.node.id
    if (nodeId == null) {
      const r = await api.post('/ea-control/sections/', cleanNode(draft.node))
      nodeId = r.data.id
      draft.node.id = nodeId
    } else {
      await api.put(`/ea-control/sections/${nodeId}/`, cleanNode(draft.node))
    }

    // 2. Слоты, 3. опции (топологически)
    for (const slot of draft.slots) {
      const slotId = await persistSlot(slot, nodeWasNew ? nodeId : null)
      if (slotId != null) await persistSlotOptions(slot, slotId)
    }

    dirty.node = dirty.slot = dirty.option = false
    await reload()
    const n = sections.value.find(s => s.id === nodeId)
    if (n) selectNode(n)
    flashSuccess('Сохранено')
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка сохранения'
  }
}

// Сохранить только выбранный слот (и его опции), не трогая узел и другие слоты.
async function commitSlot() {
  error.value = ''
  const s = selSlot.value
  if (!s) return
  if (!s._deleted) {
    const errs = validateSlotDraft(s, new Set())
    if (errs.length) {
      error.value = 'Заполните обязательные поля: ' + errs.join('; ')
      return
    }
  }
  try {
    const slotId = await persistSlot(s, draft.node ? draft.node.id : null)
    if (slotId != null) await persistSlotOptions(s, slotId)
    await reload()
    refreshSlotDraft()
    flashSuccess('Слот сохранён')
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка сохранения'
  }
}

function uniqueCode(base, taken) {
  if (!taken.has(base)) return base
  let n = 2
  while (taken.has(`${base}${n}`)) n += 1
  return `${base}${n}`
}

// Копировать выбранный слот и все его опции: коды получают суффикс `_Copy`
// (коды слотов и опций глобально уникальны). Секция берётся из текущей формы.
async function copySlot() {
  const src = selSlot.value
  if (!src) return
  error.value = ''
  try {
    const slotTaken = new Set(slots.value.map(s => s.code))
    const newCode = uniqueCode(`${(src.code || 'slot').trim()}_Copy`, slotTaken)
    const r = await api.post('/ea-control/slots/', { ...cleanSlot(src), code: newCode })
    const slotId = r.data.id

    const optTaken = new Set(options.value.map(o => o.code))
    for (const opt of (src.options || [])) {
      if (opt._deleted) continue
      const optCode = uniqueCode(`${(opt.code || 'opt').trim()}_Copy`, optTaken)
      optTaken.add(optCode)
      await api.post('/ea-control/slot-options/', { ...cleanOption(opt), code: optCode, slot: slotId })
    }

    await reload()
    refreshSlotDraft()
    flashSuccess(`Слот скопирован: ${newCode}`)
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка копирования'
  }
}

onMounted(reload)
</script>
<style scoped>
.structure-page { display: flex; height: calc(100vh - 80px); }
.left-pane { width: 300px; border-right: 1px solid #ddd; overflow: auto; padding: 12px; }
.right-pane { flex: 1; overflow: auto; padding: 12px; }
.pane-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.pane-head h3 { margin: 0; font-size: 18px; }
.node-list { display: flex; flex-direction: column; gap: 2px; }
.node-item { display: flex; gap: 6px; padding: 6px 8px; cursor: pointer; border-radius: 3px; }
.node-item:hover { background: #f0f0f0; }
.node-item.active { background: #2c6fb0; color: #fff; }
.node-item .label { flex: 1; }
.node-item .code { color: #888; font-size: 11px; }
.node-item.active .code { color: #dbe7f3; }
.node-item.new { color: #2c6fb0; font-style: italic; }
.error { color: #c00; margin-top: 8px; }
.empty { color: #999; padding: 20px; }
.save-error { background: #fdecea; color: #c62828; padding: 8px 10px; border-radius: 4px; margin-bottom: 10px; }
.save-ok { background: #eaf5ea; color: #1e7e34; padding: 8px 10px; border-radius: 4px; margin-bottom: 10px; }

.editors { display: flex; flex-direction: column; gap: 12px; }
.editor { border: 1px solid #e0e0e0; border-radius: 6px; padding: 12px; }
.editor.nested { border-color: #d0dbe8; background: #fafbfd; }
.editor-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.entity-label { color: #444; font-weight: 600; white-space: nowrap; }
.entity-name { flex: 1; min-width: 120px; padding: 5px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 15px; font-weight: 600; }
.dirty { color: #c77700; font-size: 12px; }
.del-banner { background: #fdecea; color: #c62828; padding: 6px 8px; border-radius: 3px; margin-bottom: 8px; font-size: 13px; }

.form { display: flex; flex-direction: column; gap: 8px; }
.form-row { display: flex; gap: 12px; }
.form-field { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; }
.form-field > span { flex: 0 0 96px; text-align: right; color: #444; font-size: 13px; }
.form-field > input, .form-field > select, .form-field > textarea {
  flex: 1; min-width: 0; padding: 4px 6px; border: 1px solid #ccc; border-radius: 3px; box-sizing: border-box;
}
.form-field.chk > input { flex: 0 0 auto; }

.section-picker { position: relative; flex: 1; min-width: 0; }
.sp-btn {
  width: 100%; display: flex; align-items: center; justify-content: space-between; gap: 6px;
  padding: 4px 6px; border: 1px solid #ccc; border-radius: 3px; background: #fff;
  font-size: 13px; cursor: pointer; box-sizing: border-box;
}
.sp-btn:hover { border-color: #999; }
.sp-val { flex: 1; text-align: left; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sp-caret { color: #888; font-size: 11px; }
.sp-menu {
  position: absolute; top: 100%; left: 0; right: 0; margin-top: 2px; z-index: 60;
  background: #fff; border: 1px solid #ccc; border-radius: 3px; box-shadow: 0 4px 12px rgba(0,0,0,.15);
  max-height: 280px; overflow: auto;
}
.sp-item { padding: 4px 8px; cursor: pointer; font-size: 13px; white-space: nowrap; }
.sp-item:hover { background: #eef4fb; }
.sp-item.active { background: #2c6fb0; color: #fff; }

.sub-head { display: flex; align-items: center; justify-content: space-between; margin: 14px 0 6px; }
.sub-head h4 { margin: 0; }
.ms { display: flex; flex-wrap: wrap; gap: 6px; max-height: 120px; overflow: auto; border: 1px solid #eee; padding: 4px; }
.ms-item { display: flex; gap: 4px; align-items: center; font-size: 13px; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip {
  padding: 4px 10px; border: 1px solid #ccc; border-radius: 14px; cursor: pointer;
  background: #fff; font-size: 13px;
}
.chip:hover { background: #f0f0f0; }
.chip.active { background: #2c6fb0; color: #fff; border-color: #2c6fb0; }
.chip.deleted { background: #fdecea; border-color: #c62828; color: #c62828; text-decoration: line-through; }
.del-mark { color: #c62828; font-weight: bold; }
.hint { color: #999; font-size: 12px; }
</style>
