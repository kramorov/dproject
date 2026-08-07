<template>
  <div class="bnf-overlay">
    <div class="bnf-modal">
      <div class="bnf-header">
        <h3>Ветвление: {{ form.name || form.id }}</h3>
        <button class="bnf-close" @click="$emit('cancel')">✕</button>
      </div>

      <div class="bnf-body">
        <div class="bnf-field">
          <label>Название</label>
          <input v-model="form.name" class="bnf-input" placeholder="Ветвление по типу" />
        </div>

        <div class="bnf-field">
          <label>param_name</label>
          <input v-model="form.param_name" class="bnf-input" placeholder="fitting_variety_id" @change="loadOptions" />
        </div>

        <div class="bnf-field">
          <label>Значения для ветки «ДА»</label>
          <div v-if="loading" class="bnf-hint">Загрузка опций...</div>
          <div v-else-if="branchOptions.length" class="bnf-chips">
            <label v-for="o in branchOptions" :key="o.id" class="bnf-chip" :class="{ active: matchSet.has(String(o.id)) }">
              <input type="checkbox" :checked="matchSet.has(String(o.id))" @change="toggleMatch(o.id)" />
              {{ o.name }}
            </label>
          </div>
          <button class="bnf-btn-sm" @click="loadOptions">🔄 Загрузить опции</button>
        </div>

        <div class="bnf-field">
          <label>Если ДА → узел</label>
          <select v-model="form.match_target" class="bnf-input">
            <option value="">— не выбрано —</option>
            <option v-for="n in allNodes" :key="n.id" :value="n.id">{{ n.data.name || n.id }} ({{ n.type }})</option>
          </select>
        </div>

        <div class="bnf-field">
          <label>Если НЕТ → узел</label>
          <select v-model="form.else_target" class="bnf-input">
            <option value="">— не выбрано —</option>
            <option v-for="n in allNodes" :key="n.id" :value="n.id">{{ n.data.name || n.id }} ({{ n.type }})</option>
          </select>
        </div>
      </div>

      <div class="bnf-footer">
        <button class="bnf-btn bnf-btn-cancel" @click="$emit('cancel')">Отмена</button>
        <button class="bnf-btn bnf-btn-save" @click="onSave">Сохранить</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import api from '@/shared/api'

const props = defineProps({
  node: { type: Object, required: true },
  allNodes: { type: Array, default: () => [] },
  graphCode: { type: String, default: '' },
})
const emit = defineEmits(['save', 'cancel'])

const d = props.node.data || {}
const form = reactive({
  id: props.node.id,
  name: d.name || '',
  param_name: d.param_name || '',
  match_target: d.match_target || '',
  else_target: d.else_target || '',
})
const matchSet = reactive(new Set((d.match_values || []).map(String)))
const branchOptions = ref([])
const loading = ref(false)

// Auto-load options on init
if (form.param_name) loadOptions()

async function loadOptions() {
  if (!form.param_name || !props.graphCode) return
  loading.value = true
  try {
    const { data } = await api.get(`/core/question-graph/${props.graphCode}/`)
    const entryOpts = data.entry_options || {}
    branchOptions.value = entryOpts[form.param_name] || []
  } catch (e) {
    branchOptions.value = []
  }
  loading.value = false
}

function toggleMatch(id) {
  const sid = String(id)
  if (matchSet.has(sid)) matchSet.delete(sid); else matchSet.add(sid)
}

function onSave() {
  emit('save', {
    id: props.node.id,
    name: form.name,
    param_name: form.param_name,
    match_values: [...matchSet],
    match_target: form.match_target,
    else_target: form.else_target,
  })
}
</script>

<style scoped>
.bnf-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 200; }
.bnf-modal { background: #fff; border-radius: 14px; width: 560px; max-height: 85vh; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.bnf-header { display: flex; align-items: center; padding: 14px 20px; border-bottom: 1px solid #e5e7eb; }
.bnf-header h3 { margin: 0; font-size: 16px; flex: 1; }
.bnf-close { background: none; border: none; font-size: 18px; cursor: pointer; color: #94a3b8; }
.bnf-body { padding: 16px 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; flex: 1; }
.bnf-field { display: flex; flex-direction: column; gap: 4px; }
.bnf-field label { font-size: 12px; font-weight: 600; color: #475569; }
.bnf-input { padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; }
.bnf-input:focus { border-color: #2563eb; outline: none; }
.bnf-hint { font-size: 12px; color: #94a3b8; }
.bnf-chips { display: flex; flex-wrap: wrap; gap: 4px; max-height: 200px; overflow-y: auto; border: 1px solid #e5e7eb; border-radius: 6px; padding: 8px; }
.bnf-chip { display: flex; align-items: center; gap: 4px; padding: 3px 8px; border: 1px solid #d1d5db; border-radius: 14px; font-size: 12px; cursor: pointer; background: #fff; }
.bnf-chip.active { background: #ede9fe; border-color: #a78bfa; color: #5b21b6; }
.bnf-chip input { margin: 0; accent-color: #7c3aed; }
.bnf-btn-sm { padding: 4px 10px; font-size: 12px; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 5px; cursor: pointer; color: #334155; }
.bnf-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 14px 20px; border-top: 1px solid #e5e7eb; }
.bnf-btn { padding: 8px 20px; border-radius: 7px; font-size: 13px; font-weight: 500; cursor: pointer; border: none; }
.bnf-btn-cancel { background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }
.bnf-btn-save { background: #2563eb; color: #fff; }
</style>
