<template>
  <div class="syscodes">
    <h2>Редактор системных кодировок</h2>

    <div class="tmpl-block">
      <label class="field wide"><span>Шаблон системного кода</span>
        <textarea v-model="systemCodeTemplate" rows="3"
                  @input="templateDirty = true"
                  placeholder="{model_code}-{node:GENERAL}:[{slots:GENERAL}]-…"></textarea>
      </label>
      <div class="tmpl-hint">
        Плейсхолдеры: <b>{model_code}</b> — код модели БУ;
        <b>{node:X}</b> / <b>{slot:X}</b> — X = поле <b>code</b> сущности (адрес в
        шаблоне; подставляется <b>кодировка</b> сущности, пусто — code);
        <b>{slots:X}</b> — все активные слоты узла X: кодировка слота + кодировки
        выбранных опций подряд (multi — в порядке сортировки), слоты разделяются
        <b>точкой</b>; слот без выбранного — «голый». Пусто — фолбэк
        «model_code/узел.слот+кодировки».
      </div>
      <button :disabled="savingTemplate" @click="saveAll">Сохранить</button>
      <span v-if="templateSaved" class="ok">Сохранено</span>
      <div class="tmpl-hint">
        «Сохранить» сохраняет шаблон и <b>все изменённые кодировки</b> узлов,
        слотов и опций; «✓» у строки — сохранить только эту строку.
      </div>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-for="node in tree" :key="'n' + node.id" class="node-block"
         :style="{ paddingLeft: (node.depth * 16) + 'px' }">
      <div class="node-row">
        <span class="label">{{ node.name || node.code }}</span>
        <code class="token">{{ node.code }}</code>
        <input v-if="node.id !== null" v-model="node.encoding" placeholder="кодировка"
               @input="node._dirty = true" />
        <button v-if="node.id !== null && node._dirty" @click="saveSection(node)">✓</button>
      </div>

      <div v-for="slot in node.slots" :key="'s' + slot.id" class="slot-block">
        <div class="slot-row">
          <span class="label">{{ slot.name || slot.code }}</span>
          <code class="token">{{ slot.code }}</code>
          <input v-model="slot.encoding" placeholder="кодировка" @input="slot._dirty = true" />
          <button v-if="slot._dirty" @click="saveSlot(slot)">✓</button>
        </div>

        <div class="opt-table">
          <div class="opt-head">
            <span>Название опции</span>
            <span>Кодировка</span>
            <span></span>
          </div>
          <div v-for="opt in slot.options" :key="'o' + opt.id" class="opt-row">
            <span class="opt-name">{{ opt.name || opt.code }}</span>
            <input v-model="opt.encoding" placeholder="кодировка" @input="opt._dirty = true" />
            <button v-if="opt._dirty" @click="saveOption(opt)">✓</button>
          </div>
          <div v-if="!slot.options.length" class="opt-empty">Опций нет</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * Редактор системных кодировок: шаблон системного кода (синглтон CuCodeSettings)
 * + кодировки (encoding) узлов/слотов и опций.
 *
 * Узлы и слоты: ``code`` — адрес-плейсхолдер в шаблоне (правится в
 * «Конфигураторе опций», здесь — read-only бейдж); ``encoding`` — кодировка,
 * подставляемая в системный код (пусто — фолбэк на code), редактируется здесь.
 * Опция даёт только кодировку (1-2 говорящих символа, уникальна внутри слота);
 * ext_encoding — кодировка конкретного БУ (вкладка «Кодировки» в «Редакторе БУ»).
 * Каждый слот — отдельной строкой, опции — таблицей: название / кодировка.
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
const templateDirty = ref(false)

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
      id: null, code: '', name: 'Без раздела', depth: 0,
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

async function saveAll() {
  error.value = ''
  templateSaved.value = false
  savingTemplate.value = true
  const tasks = []
  if (templateDirty.value) {
    tasks.push(api.put('/ea-control/code-settings/', {
      system_code_template: systemCodeTemplate.value,
    }).then(({ data }) => {
      systemCodeTemplate.value = data.system_code_template || ''
      templateDirty.value = false
    }))
  }
  for (const node of tree.value) {
    if (node.id !== null && node._dirty) {
      tasks.push(api.patch(`/ea-control/sections/${node.id}/`, {
        encoding: node.encoding || '',
      }).then(() => { node._dirty = false }))
    }
    for (const slot of node.slots) {
      if (slot._dirty) {
        tasks.push(api.patch(`/ea-control/slots/${slot.id}/`, {
          encoding: slot.encoding || '',
        }).then(() => { slot._dirty = false }))
      }
      for (const opt of slot.options) {
        if (opt._dirty) {
          tasks.push(api.patch(`/ea-control/slot-options/${opt.id}/`, {
            encoding: opt.encoding || '',
          }).then(() => { opt._dirty = false }))
        }
      }
    }
  }
  if (!tasks.length) {
    savingTemplate.value = false
    return
  }
  try {
    await Promise.all(tasks)
    templateSaved.value = true
    await reload()
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка сохранения'
  } finally {
    savingTemplate.value = false
  }
}

async function saveSection(node) {
  error.value = ''
  try {
    await api.patch(`/ea-control/sections/${node.id}/`, { encoding: node.encoding || '' })
    node._dirty = false
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка сохранения кодировки узла'
  }
}

async function saveSlot(slot) {
  error.value = ''
  try {
    await api.patch(`/ea-control/slots/${slot.id}/`, { encoding: slot.encoding || '' })
    slot._dirty = false
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка сохранения кодировки слота'
  }
}

async function saveOption(opt) {
  error.value = ''
  try {
    await api.patch(`/ea-control/slot-options/${opt.id}/`, {
      encoding: opt.encoding || '',
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
.node-row { display: flex; gap: 8px; align-items: center; margin: 3px 0 8px; }
.node-row .label { width: 280px; font-size: 13px; color: #333; }
.node-row input { width: 180px; }
.node-row button { padding: 3px 8px; }
.token { font-size: 12px; color: #2c6fb0; background: #f2f6fa; padding: 1px 6px; border-radius: 3px; }

/* каждый слот — отдельной строкой (блоком) */
.slot-block { margin: 0 0 10px; }
.slot-row { display: flex; gap: 8px; align-items: center; margin: 3px 0; }
.slot-row .label { width: 280px; font-size: 13px; color: #333; }
.slot-row input { width: 180px; }
.slot-row button { padding: 3px 8px; }

/* опции слота — таблица: название / кодировка */
.opt-table { margin-left: 16px; border: 1px solid #eee; border-radius: 4px; }
.opt-head, .opt-row {
  display: grid;
  grid-template-columns: minmax(240px, 1fr) 130px 40px;
  gap: 6px;
  align-items: center;
  padding: 3px 8px;
}
.opt-head {
  font-size: 11px;
  color: #777;
  background: #f5f5f5;
  border-bottom: 1px solid #ddd;
  border-radius: 4px 4px 0 0;
}
.opt-row + .opt-row { border-top: 1px solid #f2f2f2; }
.opt-name { font-size: 12px; color: #333; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.opt-row input { width: 100%; }
.opt-row button { padding: 3px 8px; }
.opt-empty { padding: 4px 8px; font-size: 12px; color: #999; }
</style>