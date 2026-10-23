<template>
  <div class="structure-page">
    <!-- ЛЕВАЯ ЧАСТЬ: выбор узла -->
    <div class="left-pane">
      <div class="pane-head">
        <h3>Узлы</h3>
        <button @click="onAddNode">+ Добавить узел</button>
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
        <!-- УЗЕЛ -->
        <div class="editor">
          <div class="editor-head">
            <span class="entity-label">Узел:</span>
            <input class="entity-name" v-model="draft.node.name" placeholder="Название узла"
                   @input="markDirty('node')" />
            <span v-if="hasChanges" class="dirty">не сохранено</span>
            <EditorActions
              :can-save="hasChanges"
              :deletable="true"
              :delete-label="nodeDeleteLabel"
              :pending-delete="draft.node._deleted"
              @save="commitAll"
              @delete="toggleDeleteNode" />
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
            <button @click="addSlot">+ Добавить слот</button>
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
              <EditorActions
                :show-save="false"
                delete-label="Удалить слот"
                :pending-delete="selSlot._deleted"
                @delete="toggleDeleteSlot" />
            </div>
            <div v-if="selSlot._deleted" class="del-banner">Слот будет удалён при сохранении.</div>

            <div class="form" @input="markDirty('slot')" @change="markDirty('slot')">
              <div class="form-row">
                <label class="form-field"><span>Код</span><input v-model="selSlot.code" /></label>
                <label class="form-field"><span>Родитель</span>
                  <select v-model="selSlot.section">
                    <option :value="null">— без секции —</option>
                    <option v-for="o in sectionOptions" :key="o.id" :value="o.id">{{ o.label }}</option>
                  </select>
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
              <button @click="addOption">+ Добавить опцию</button>
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
                <EditorActions
                  :show-save="false"
                  delete-label="Удалить опцию"
                  :pending-delete="selOption._deleted"
                  @delete="toggleDeleteOption" />
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
                      <option value="signal_type">Тип сигнала</option>
                      <option value="unit">БУ</option>
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
                <div v-else-if="selOption.kind === 'signal_type'" class="form-row">
                  <label class="form-field"><span>Тип сигнала</span>
                    <select v-model="selOption.signal_type">
                      <option :value="null">— —</option>
                      <option v-for="o in dicts.signalTypes" :key="o.id" :value="o.id">{{ o.label }}</option>
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
import { computed, onMounted, reactive, ref } from 'vue'
import api from '@/shared/api'
import EditorActions from '@/components/EditorActions.vue'

const loading = ref(false)
const error = ref('')
const sections = ref([])
const slots = ref([])
const options = ref([])
const dicts = reactive({
  controlSignals: [], feedbackSignals: [], protocols: [], devices: [],
  heaterSupplies: [], signalPowers: [], controlLogics: [], signalTypes: [],
  units: [],
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
  (draft.node && draft.node.id == null) ? 'Отменить создание' : 'Удалить узел')

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

const sectionOptions = computed(() =>
  sections.value.map(s => ({ id: s.id, label: s.name || s.code })))

const hasPendingDeletes = computed(() => {
  if (draft.node && draft.node._deleted) return true
  return draft.slots.some(s => s._deleted || (s.options || []).some(o => o._deleted))
})

const hasChanges = computed(() =>
  dirty.node || dirty.slot || dirty.option || hasPendingDeletes.value)

function markDirty(kind) {
  dirty[kind] = true
}

function dictList(rows) {
  return rows.map(o => ({ id: o.id, label: o.name || o.code || String(o.id) }))
}

async function reload() {
  loading.value = true
  error.value = ''
  try {
    const [s, sl, o, units, ctl, fb, proto, dev, heater, power, logic, stype] =
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
        api.get('/ea-control/signal-types/'),
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
    dicts.signalTypes = dictList(stype.data.results || stype.data || [])
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
    signal_type: o.signal_type, control_unit: o.control_unit, device: o.device,
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
    signal_type: null, control_unit: null, device: null,
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
  o.signal_type = null
  o.control_unit = null
  o.device = null
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

function validateDraft() {
  const errs = []
  if (!draft.node.code || !draft.node.code.trim()) errs.push('узел: код')
  if (!draft.node.name || !draft.node.name.trim()) errs.push('узел: название')
  for (const slot of draft.slots) {
    if (slot._deleted) continue
    const slotLabel = slot.name || slot.code || 'новый слот'
    if (!slot.code || !slot.code.trim()) errs.push(`слот «${slotLabel}»: код`)
    for (const opt of (slot.options || [])) {
      if (opt._deleted) continue
      if (!opt.code || !opt.code.trim()) errs.push(`опция в слоте «${slotLabel}»: код`)
      if ((opt.kind === 'none' || opt.kind === 'pair') && (!opt.name || !opt.name.trim())) {
        errs.push(`опция в слоте «${slotLabel}»: название (обязательно для none/pair)`)
      }
    }
  }
  return errs
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
      if (slot._deleted) {
        if (slot.id != null) await api.delete(`/ea-control/slots/${slot.id}/`)
        continue
      }
      let slotId = slot.id
      if (slotId == null) {
        const section = (slot.section == null && nodeWasNew) ? nodeId : slot.section
        const r = await api.post('/ea-control/slots/',
          { ...cleanSlot(slot), section })
        slotId = r.data.id
        slot.id = slotId
      } else {
        await api.put(`/ea-control/slots/${slotId}/`, cleanSlot(slot))
      }
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

    dirty.node = dirty.slot = dirty.option = false
    await reload()
    const n = sections.value.find(s => s.id === nodeId)
    if (n) selectNode(n)
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка сохранения'
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

.sub-head { display: flex; align-items: center; justify-content: space-between; margin: 14px 0 6px; }
.sub-head h4 { margin: 0; }
.sub-head button { padding: 4px 10px; cursor: pointer; }
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
