<template>
  <div class="syscodes">
    <h2>Редактор системных кодировок</h2>

    <div class="tmpl-block">
      <label class="field wide"><span>Шаблон системного кода</span>
        <textarea v-model="systemCodeTemplate" rows="3"
                  placeholder="{node:SENSOR}:[{slots:SENSOR}]-{node:GENERAL}:[{slots:GENERAL}]"></textarea>
      </label>
      <div class="tmpl-hint">
        Плейсхолдеры: <b>{node:X}</b> — токен узла, <b>{slot:X}</b> — токен слота,
        <b>{opt:X}</b> — токен опции, <b>{slots:X}</b> — разворот слотов узла
        (slot_token+opt_token, в порядке дерева). Пусто — фоллбэк «узел.слот.опция» через «/».
      </div>
      <button :disabled="savingTemplate" @click="saveTemplate">Сохранить шаблон</button>
      <span v-if="templateSaved" class="ok">Сохранено</span>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-for="node in tree" :key="'n' + node.id" class="node-block"
         :style="{ paddingLeft: (node.depth * 16) + 'px' }">
      <div class="node-row">
        <span class="label">{{ node.name || node.code }}</span>
        <input v-model="node.placeholder" placeholder="плейсхолдер" @input="node._dirty = true" />
        <button v-if="node._dirty" @click="saveSection(node)">✓</button>
      </div>

      <div v-for="slot in node.slots" :key="'s' + slot.id" class="slot-row"
           :style="{ paddingLeft: ((node.depth + 1) * 16) + 'px' }">
        <span class="label">{{ slot.name || slot.code }}</span>
        <input v-model="slot.placeholder" placeholder="плейсхолдер" @input="slot._dirty = true" />
        <button v-if="slot._dirty" @click="saveSlot(slot)">✓</button>

        <div v-for="opt in slot.options" :key="'o' + opt.id" class="opt-row"
             :style="{ paddingLeft: ((node.depth + 2) * 16) + 'px' }">
          <span class="label">{{ opt.name || opt.code }}</span>
          <input v-model="opt.placeholder" placeholder="плейсхолдер" @input="opt._dirty = true" />
          <input v-model="opt.encoding" placeholder="encoding" @input="opt._dirty = true" />
          <input v-model="opt.ext_encoding" placeholder="ext" @input="opt._dirty = true" />
          <button v-if="opt._dirty" @click="saveOption(opt)">✓</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * Редактор системных кодировок: шаблон системного кода (синглтон CuCodeSettings)
 * + плейсхолдеры узлов/слотов и плейсхолдер/encoding/ext_encoding опций.
 */
import { computed, onMounted, reactive, ref } from 'vue'
import api from '@/shared/api'

const systemCodeTemplate = ref('')
const sections = ref([])
const slots = ref([])
const options = ref([])
const error = ref('')
const savingTemplate = ref(false)
const templateSaved = ref(false)

const tree = computed(() => {
  const byParent = {}
  for (const n of sections.value) {
    if (!byParent[n.parent || 0]) byParent[n.parent || 0] = []
    byParent[n.parent || 0].push(n)
  }
  const slotsBySection = {}
  for (const s of slots.value) {
    if (!slotsBySection[s.section]) slotsBySection[s.section] = []
    slotsBySection[s.section].push(s)
  }
  const optionsBySlot = {}
  for (const o of options.value) {
    if (!optionsBySlot[o.slot]) optionsBySlot[o.slot] = []
    optionsBySlot[o.slot].push(o)
  }
  const wrapSlot = s => reactive({
    ...s, _dirty: false,
    options: (optionsBySlot[s.id] || []).map(o => reactive({ ...o, _dirty: false })),
  })
  const out = []
  const walk = (parentId, depth) => {
    for (const n of (byParent[parentId] || [])) {
      out.push(reactive({
        ...n, depth, _dirty: false,
        slots: (slotsBySection[n.id] || []).map(wrapSlot),
      }))
      walk(n.id, depth + 1)
    }
  }
  walk(0, 0)
  // слоты без раздела (например, слот-селектор типа control_unit)
  const orphanSlots = (slotsBySection[null] || []).map(wrapSlot)
  if (orphanSlots.length) {
    out.push(reactive({
      id: null, code: '', name: 'Без раздела', depth: 0, _dirty: false,
      slots: orphanSlots,
    }))
  }
  return out
})

async function reload() {
  error.value = ''
  try {
    const [cs, s, sl, o] = await Promise.all([
      api.get('/ea-control/code-settings/'),
      api.get('/ea-control/sections/'),
      api.get('/ea-control/slots/'),
      api.get('/ea-control/slot-options/'),
    ])
    systemCodeTemplate.value = cs.data.system_code_template || ''
    sections.value = s.data.results || s.data || []
    slots.value = sl.data.results || sl.data || []
    options.value = o.data.results || o.data || []
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка загрузки'
  }
}

async function saveTemplate() {
  error.value = ''
  templateSaved.value = false
  savingTemplate.value = true
  try {
    const { data } = await api.put('/ea-control/code-settings/', {
      system_code_template: systemCodeTemplate.value,
    })
    systemCodeTemplate.value = data.system_code_template || ''
    templateSaved.value = true
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка сохранения шаблона'
  } finally {
    savingTemplate.value = false
  }
}

async function saveSection(node) {
  error.value = ''
  try {
    await api.patch(`/ea-control/sections/${node.id}/`, { placeholder: node.placeholder || '' })
    node._dirty = false
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка сохранения узла'
  }
}

async function saveSlot(slot) {
  error.value = ''
  try {
    await api.patch(`/ea-control/slots/${slot.id}/`, { placeholder: slot.placeholder || '' })
    slot._dirty = false
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка сохранения слота'
  }
}

async function saveOption(opt) {
  error.value = ''
  try {
    await api.patch(`/ea-control/slot-options/${opt.id}/`, {
      placeholder: opt.placeholder || '',
      encoding: opt.encoding || '',
      ext_encoding: opt.ext_encoding || '',
    })
    opt._dirty = false
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка сохранения опции'
  }
}

onMounted(reload)
</script>

<style scoped>
.syscodes { padding: 12px; max-width: 1100px; }
h2 { margin: 0 0 10px; }
.tmpl-block { border: 1px solid #ddd; border-radius: 6px; padding: 10px; margin-bottom: 14px; }
.field { display: flex; flex-direction: column; gap: 4px; margin-bottom: 8px; }
.field span { font-size: 12px; color: #555; }
textarea, input { padding: 5px 7px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; }
.tmpl-hint { font-size: 12px; color: #666; margin: 6px 0; }
button { padding: 6px 12px; cursor: pointer; }
.ok { color: #2c6fb0; margin-left: 8px; }
.error { color: #c00; margin: 6px 0; }
.node-block { border: 1px solid #eee; border-radius: 6px; padding: 6px; margin-bottom: 8px; }
.node-row, .slot-row, .opt-row { display: flex; gap: 6px; align-items: center; margin: 3px 0; }
.node-row .label, .slot-row .label, .opt-row .label { width: 280px; font-size: 13px; color: #333; }
.node-row input { width: 180px; }
.slot-row input { width: 180px; }
.opt-row input { width: 130px; }
.opt-row input:first-of-type { width: 180px; }
.node-row button, .slot-row button, .opt-row button { padding: 3px 8px; }
</style>
