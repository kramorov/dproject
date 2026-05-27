<!-- shared/components/ChipList.vue — строки выбранных сущностей с чекбоксами -->
<template>
  <div class="cl-root">
    <label v-if="label" class="cl-label">{{ label }}</label>
    <div class="cl-table-wrap">
      <table class="cl-tbl" v-if="items.length">
        <thead>
          <tr>
            <th class="cl-th-chk">☐</th>
            <th>Код</th>
            <th>Название</th>
            <th class="cl-th-act"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id" class="cl-row"
            :class="{ sel: batchIds.includes(item.id) }"
            @click="toggleBatch(item.id)">
            <td class="cl-td-chk">
              <span v-if="batchIds.includes(item.id)">☑</span>
              <span v-else>☐</span>
            </td>
            <td class="cl-td-code">{{ item.code || '—' }}</td>
            <td>{{ item.name || '—' }}</td>
            <td class="cl-td-act">
              <button class="cl-del-one" @click.stop="$emit('remove', item.id)" title="Удалить">✕</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="cl-empty">Нет выбранных элементов</div>
    </div>
    <div class="cl-actions">
      <button class="cl-pick-btn" @click="$emit('pick')">📋 {{ pickLabel }}</button>
      <button v-if="items.length"
        class="cl-del-btn"
        :disabled="!batchIds.length"
        @click="doBatchRemove">
        🗑 Удалить выбранные ({{ batchIds.length }})
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] },
  label: { type: String, default: '' },
  pickLabel: { type: String, default: 'Подбор' },
})
const emit = defineEmits(['pick', 'remove', 'removeBatch'])

const batchIds = ref([])

function toggleBatch(id) {
  const idx = batchIds.value.indexOf(id)
  if (idx >= 0) batchIds.value.splice(idx, 1)
  else batchIds.value.push(id)
}

function doBatchRemove() {
  emit('removeBatch', [...batchIds.value])
  batchIds.value = []
}
</script>

<style scoped>
.cl-root { display: flex; flex-direction: column; gap: 6px; }
.cl-label { font-size: 13px; font-weight: 500; color: #374151; }
.cl-table-wrap { border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; }
.cl-tbl { width: 100%; border-collapse: collapse; font-size: 13px; }
.cl-tbl th { text-align: left; padding: 6px 8px; background: #f9fafb; border-bottom: 1px solid #e5e7eb; color: #6b7280; font-weight: 500; font-size: 12px; }
.cl-th-chk { width: 32px; text-align: center; }
.cl-th-act { width: 36px; }
.cl-td-chk { width: 32px; text-align: center; font-size: 13px; cursor: pointer; }
.cl-td-code { font-family: monospace; font-size: 12px; color: #6b7280; white-space: nowrap; }
.cl-td-act { width: 36px; text-align: center; }
.cl-row { cursor: pointer; transition: background .1s; }
.cl-row:hover { background: #f9fafb; }
.cl-row.sel { background: #eff6ff; }
.cl-tbl td { padding: 5px 8px; border-bottom: 1px solid #f3f4f6; }
.cl-del-one { background: none; border: none; color: #9ca3af; cursor: pointer; font-size: 13px; padding: 2px 4px; }
.cl-del-one:hover { color: #dc2626; }
.cl-empty { padding: 16px; text-align: center; color: #9ca3af; font-size: 13px; }
.cl-actions { display: flex; gap: 6px; align-items: center; }
.cl-pick-btn { padding: 5px 14px; border: 1px dashed #2563eb; border-radius: 6px; background: #fff; color: #2563eb; cursor: pointer; font-size: 13px; }
.cl-pick-btn:hover { background: #eff6ff; }
.cl-del-btn { padding: 5px 14px; border: 1px solid #dc2626; border-radius: 6px; background: #fff; color: #dc2626; cursor: pointer; font-size: 13px; }
.cl-del-btn:hover:not(:disabled) { background: #fef2f2; }
.cl-del-btn:disabled { opacity: .4; cursor: default; border-color: #d1d5db; color: #9ca3af; }
</style>
