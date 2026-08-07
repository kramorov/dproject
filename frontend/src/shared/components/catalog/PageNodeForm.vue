<template>
  <div class="pnf-overlay">
    <div class="pnf-modal">
      <div class="pnf-header">
        <h3>Страница: {{ form.name || form.id }}</h3>
        <button class="pnf-close" @click="$emit('cancel')">✕</button>
      </div>

      <div class="pnf-body">
        <div class="pnf-field">
          <label>Название страницы</label>
          <input v-model="form.name" class="pnf-input" placeholder="Выбор типа" />
        </div>

        <div class="pnf-field">
          <label>Вопросы</label>
          <div class="pnf-params-list">
            <div v-for="(p, i) in form.params" :key="i" class="pnf-param-row">
              <span class="pnf-order">{{ p.order || i + 1 }}</span>
              <input v-model="p.title" class="pnf-input pnf-input-sm" placeholder="Заголовок вопроса" />
              <input v-model="p.param_name" class="pnf-input pnf-input-sm" placeholder="param_name" />
              <button class="pnf-btn-del" @click="form.params.splice(i,1)">✕</button>
            </div>
          </div>
          <button class="pnf-btn-sm" @click="form.params.push({order: form.params.length+1, title:'', param_name:''})">+ вопрос</button>
        </div>

        <div class="pnf-field">
          <label>Следующий узел</label>
          <select v-model="form.next_node" class="pnf-input">
            <option value="">— конец —</option>
            <option v-for="n in allNodes" :key="n.id" :value="n.id">{{ n.data.name || n.id }} ({{ n.type }})</option>
          </select>
        </div>

        <div class="pnf-field">
          <label><input type="checkbox" v-model="form.isEntry" /> Входной узел</label>
        </div>
      </div>

      <div class="pnf-footer">
        <button class="pnf-btn pnf-btn-cancel" @click="$emit('cancel')">Отмена</button>
        <button class="pnf-btn pnf-btn-save" @click="onSave">Сохранить</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  node: { type: Object, required: true },
  allNodes: { type: Array, default: () => [] },
  isEntry: { type: Boolean, default: false },
  nextNode: { type: String, default: '' },
})
const emit = defineEmits(['save', 'cancel'])

const form = ref(initForm())

function initForm() {
  const d = props.node.data || {}
  return {
    id: props.node.id,
    name: d.name || '',
    params: (d.params || []).map(p => ({ ...p })),
    next_node: props.nextNode || d.next_node || '',
    isEntry: props.isEntry,
  }
}

function onSave() {
  emit('save', {
    id: props.node.id,
    name: form.value.name,
    params: form.value.params.map((p, i) => ({ ...p, order: p.order || i + 1 })),
    next_node: form.value.next_node,
    isEntry: form.value.isEntry,
  })
}
</script>

<style scoped>
.pnf-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 200; }
.pnf-modal { background: #fff; border-radius: 14px; width: 560px; max-height: 85vh; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.pnf-header { display: flex; align-items: center; padding: 14px 20px; border-bottom: 1px solid #e5e7eb; }
.pnf-header h3 { margin: 0; font-size: 16px; flex: 1; }
.pnf-close { background: none; border: none; font-size: 18px; cursor: pointer; color: #94a3b8; }
.pnf-body { padding: 16px 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; flex: 1; }
.pnf-field { display: flex; flex-direction: column; gap: 4px; }
.pnf-field label { font-size: 12px; font-weight: 600; color: #475569; }
.pnf-input { padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; }
.pnf-input:focus { border-color: #2563eb; outline: none; }
.pnf-input-sm { flex: 1; }
.pnf-params-list { display: flex; flex-direction: column; gap: 4px; }
.pnf-param-row { display: flex; gap: 6px; align-items: center; }
.pnf-order { width: 22px; text-align: center; font-size: 12px; font-weight: 600; color: #94a3b8; }
.pnf-btn-del { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 14px; }
.pnf-btn-del:hover { color: #dc2626; }
.pnf-btn-sm { padding: 4px 10px; font-size: 12px; background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 5px; cursor: pointer; color: #334155; }
.pnf-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 14px 20px; border-top: 1px solid #e5e7eb; }
.pnf-btn { padding: 8px 20px; border-radius: 7px; font-size: 13px; font-weight: 500; cursor: pointer; border: none; }
.pnf-btn-cancel { background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }
.pnf-btn-save { background: #2563eb; color: #fff; }
</style>
