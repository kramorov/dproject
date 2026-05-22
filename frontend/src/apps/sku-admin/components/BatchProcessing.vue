<template>
  <div>
    <!-- Фильтры -->
    <div class="fl">
      <input v-model="codeFilter" placeholder="Код (подстрока)..." class="fi" style="width:180px" />
      <select v-model="eqTypeFilter" class="fi"><option value="">Тип оборудования</option>
        <option value="null">— Не указано</option>
        <option v-for="t in opts.equipmentTypes" :key="t.id" :value="t.id">{{ t.name }}</option></select>
      <select v-model="brandFilter" class="fi"><option value="">Бренд</option>
        <option value="null">— Не указано</option>
        <option v-for="b in opts.brands" :key="b.id" :value="b.id">{{ b.name }}</option></select>
      <button @click="doFilter" class="btn-action">Отобрать по фильтрам</button>
    </div>

    <!-- Панель действий -->
    <div class="act-bar">
      <button @click="toggleAll" class="btn-sm">{{ allSelected ? 'Снять выделение' : 'Выделить всё' }}</button>
      <span class="sel-info">Выделено: {{ selectedIds.size }} / {{ items.length }}</span>
      <select v-model="setEqType" class="fi"><option :value="null">Тип: не менять</option>
        <option v-for="t in opts.equipmentTypes" :key="t.id" :value="t.id">{{ t.name }}</option></select>
      <select v-model="setBrand" class="fi"><option :value="null">Бренд: не менять</option>
        <option v-for="b in opts.brands" :key="b.id" :value="b.id">{{ b.name }}</option></select>
      <button @click="doSave" class="btn-action" :disabled="selectedIds.size===0||saving">
        {{ saving ? 'Сохранение...' : 'Записать' }}
      </button>
    </div>

    <!-- Таблица -->
    <div v-if="loading" class="st">Загрузка...</div>
    <table v-else class="tb">
      <thead><tr>
        <th style="width:40px"><input type="checkbox" :checked="allSelected" @change="toggleAll" /></th>
        <th>Код</th><th>Название</th><th>Тип оборудования</th><th>Бренд</th><th>Акт.</th>
      </tr></thead>
      <tbody>
        <tr v-for="s in items" :key="s.id" :class="{sel:selectedIds.has(s.id)}">
          <td><input type="checkbox" :checked="selectedIds.has(s.id)" @change="toggleOne(s.id)" /></td>
          <td class="code">{{ s.code }}</td>
          <td>{{ s.name||'—' }}</td>
          <td>{{ s.equipment_type_name||'—' }}</td>
          <td>{{ s.brand_name||'—' }}</td>
          <td>{{ s.is_active?'✓':'' }}</td>
        </tr>
      </tbody>
    </table>
    <div v-if="items.length===0 && !loading" class="st">Нет записей по фильтрам</div>
    <div v-if="msg" class="msg" :class="msgType">{{ msg }}</div>
  </div>
</template>

<script setup>
import { ref, reactive, inject, computed, onMounted } from 'vue'
import skuApi from '../api'

const opts = inject('opts')

const items = ref([]), loading = ref(false), saving = ref(false)
const codeFilter = ref(''), eqTypeFilter = ref(''), brandFilter = ref('')
const selectedIds = ref(new Set())
const setEqType = ref(null), setBrand = ref(null)
const msg = ref(''), msgType = ref('ok')

const allSelected = computed(() => items.value.length > 0 && selectedIds.value.size === items.value.length)

function toggleOne(id) {
  const s = new Set(selectedIds.value)
  if (s.has(id)) s.delete(id); else s.add(id)
  selectedIds.value = s
}

function toggleAll() {
  if (allSelected.value) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(items.value.map(x => x.id))
  }
}

async function doFilter() {
  loading.value = true; msg.value = ''
  try {
    const p = {}
    if (codeFilter.value) p.search = codeFilter.value
    if (eqTypeFilter.value) p.equipment_type_id = eqTypeFilter.value
    if (brandFilter.value) p.brand_id = brandFilter.value
    const r = await skuApi.list(p)
    items.value = r.data.data || []
    selectedIds.value = new Set()  // сбрасываем выделение при новом фильтре
  } finally { loading.value = false }
}

async function doSave() {
  if (selectedIds.value.size === 0) return
  saving.value = true; msg.value = ''
  try {
    const data = { ids: [...selectedIds.value] }
    if (setEqType.value !== null) data.equipment_type_id = setEqType.value
    if (setBrand.value !== null) data.brand_id = setBrand.value
    const r = await skuApi.batchUpdate(data)
    msg.value = `Обновлено: ${r.data.updated} записей`
    msgType.value = 'ok'
    selectedIds.value = new Set()
    await doFilter()  // обновить список
  } catch (e) {
    msg.value = e.displayMessage || e.message || 'Ошибка'
    msgType.value = 'err'
  } finally { saving.value = false }
}

onMounted(doFilter)
</script>

<style scoped>
.fl{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;align-items:center}
.fi{padding:5px 8px;border:1px solid #d1d5db;border-radius:5px;font-size:13px}
.btn-action{padding:5px 14px;background:#2563eb;color:#fff;border:none;border-radius:5px;cursor:pointer;font-size:13px}
.btn-action:hover{background:#1d4ed8}
.btn-action:disabled{opacity:.5;cursor:default}
.act-bar{display:flex;gap:8px;margin-bottom:10px;align-items:center;flex-wrap:wrap}
.btn-sm{padding:4px 10px;border:1px solid #d1d5db;border-radius:4px;background:#fff;cursor:pointer;font-size:12px}
.btn-sm:hover{background:#f3f4f6}
.sel-info{font-size:13px;color:#6b7280}
.tb{width:100%;border-collapse:collapse;font-size:13px}
.tb th{text-align:left;padding:6px 10px;background:#f9fafb;border-bottom:2px solid #e5e7eb;color:#6b7280;font-weight:500}
.tb td{padding:6px 10px;border-bottom:1px solid #f3f4f6}
.code{font-family:monospace;font-weight:500}
tr.sel{background:#eff6ff}
.st{text-align:center;padding:40px;color:#6b7280}
.msg{padding:8px 12px;border-radius:5px;font-size:13px;margin-top:8px}
.msg.ok{background:#ecfdf5;color:#065f46}
.msg.err{background:#fef2f2;color:#991b1b}
</style>
