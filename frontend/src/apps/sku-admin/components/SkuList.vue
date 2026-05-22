<template>
  <div>
    <div class="fl">
      <input v-model="search" placeholder="Поиск по коду/названию..." @input="load" class="fi" />
      <select v-model="eqType" @change="load" class="fi"><option value="">Тип оборудования</option>
        <option v-for="t in opts.equipmentTypes" :key="t.id" :value="t.id">{{ t.name }}</option></select>
      <select v-model="brand" @change="load" class="fi"><option value="">Бренд</option>
        <option v-for="b in opts.brands" :key="b.id" :value="b.id">{{ b.name }}</option></select>
      <button @click="openForm(null)" class="btn-add">+ Создать</button>
    </div>
    <div v-if="loading" class="st">Загрузка...</div>
    <table v-else class="tb">
      <thead><tr>
        <th>Код</th><th>Название</th><th>Тип</th><th>Бренд</th><th>Цен</th><th>Акт.</th><th></th>
      </tr></thead>
      <tbody>
        <tr v-for="s in items" :key="s.id">
          <td class="code">{{ s.code }}</td>
          <td>{{ s.name||'—' }}</td>
          <td>{{ s.equipment_type_name||'—' }}</td>
          <td>{{ s.brand_name||'—' }}</td>
          <td>{{ s.price_count||0 }}</td>
          <td>{{ s.is_active?'✓':'' }}</td>
          <td><button @click="openForm(s)" class="btn-edit">✎</button></td>
        </tr>
      </tbody>
    </table>
    <div v-if="items.length===0 && !loading" class="st">Ничего не найдено</div>
  </div>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'
import skuApi from '../api'

const opts = inject('opts')
const emit = defineEmits(['edit'])

const items = ref([]), loading = ref(false)
const search = ref(''), eqType = ref(''), brand = ref('')

async function load() {
  loading.value = true
  try {
    const p = {}
    if (search.value) p.search = search.value
    if (eqType.value) p.equipment_type_id = eqType.value
    if (brand.value) p.brand_id = brand.value
    const r = await skuApi.list(p)
    items.value = r.data.data || []
  } finally { loading.value = false }
}

function openForm(sku) { emit('edit', sku) }

onMounted(load)
defineExpose({ load })
</script>

<style scoped>
.fl{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;align-items:center}
.fi{padding:5px 8px;border:1px solid #d1d5db;border-radius:5px;font-size:13px}
.btn-add{padding:5px 14px;background:#2563eb;color:#fff;border:none;border-radius:5px;cursor:pointer;font-size:13px}
.btn-add:hover{background:#1d4ed8}
.tb{width:100%;border-collapse:collapse;font-size:13px}
.tb th{text-align:left;padding:6px 10px;background:#f9fafb;border-bottom:2px solid #e5e7eb;color:#6b7280;font-weight:500}
.tb td{padding:6px 10px;border-bottom:1px solid #f3f4f6}
.code{font-family:monospace;font-weight:500}
.btn-edit{padding:2px 8px;border:1px solid #d1d5db;border-radius:3px;background:#fff;cursor:pointer;font-size:12px}
.btn-edit:hover{background:#f3f4f6}
.st{text-align:center;padding:40px;color:#6b7280}
</style>
