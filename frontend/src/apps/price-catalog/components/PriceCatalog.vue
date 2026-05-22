<template>
  <div>
    <div class="fl">
      <input v-model="search" placeholder="Поиск..." @input="load" class="fi" />
      <select v-model="eqType" @change="load" class="fi"><option value="">Тип оборудования</option>
        <option v-for="t in opts.equipmentTypes" :key="t.id" :value="t.id">{{ t.name }}</option></select>
      <select v-model="brand" @change="load" class="fi"><option value="">Бренд</option>
        <option v-for="b in opts.brands" :key="b.id" :value="b.id">{{ b.name }}</option></select>
      <select v-model="variety" @change="load" class="fi"><option value="">Вид цены</option>
        <option v-for="v in opts.varieties" :key="v.id" :value="v.id">{{ v.name }}</option></select>
      <select v-model="currency" @change="load" class="fi"><option value="">Валюта</option>
        <option v-for="c in opts.currencies" :key="c.id" :value="c.id">{{ c.code }}</option></select>
      <input v-model="dateFrom" type="date" @change="load" class="fi" />
      <input v-model="dateTo" type="date" @change="load" class="fi" />
      <label class="cb"><input type="checkbox" v-model="currentOnly" @change="load"/> Актуальные</label>
    </div>
    <div v-if="loading" class="st">Загрузка...</div>
    <table v-else class="tb">
      <thead><tr><th>Название</th><th>Код</th><th>Вид</th><th>Валюта</th><th>Цена</th><th>Дата</th><th>Акт.</th></tr></thead>
      <tbody>
        <tr v-for="p in items" :key="p.id">
          <td>{{ p.name||'—' }}</td><td>{{ p.code||'—' }}</td>
          <td>{{ p.price_variety_name||p.price_variety?.name||'—' }}</td>
          <td>{{ p.currency_symbol||p.currency?.symbol||'' }} {{ p.currency_name||p.currency?.name||'' }}</td>
          <td class="pr">{{ p.price }}</td><td>{{ p.price_date?.slice(0,10)||'—' }}</td>
          <td>{{ p.is_current?'✓':'' }}</td>
        </tr>
      </tbody>
    </table>
    <div v-if="items.length===0 && !loading" class="st">Ничего не найдено</div>
  </div>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'
import priceApi from '../api'

const opts = inject('opts')

const items = ref([])
const loading = ref(false)
const search = ref(''), variety = ref(''), currency = ref(''), dateFrom = ref(''), dateTo = ref(''), currentOnly = ref(false)
const eqType = ref(''), brand = ref('')

async function load() {
  loading.value = true
  try {
    const params = {}
    if (search.value) params.search = search.value
    if (variety.value) params.price_variety_id = variety.value
    if (currency.value) params.currency_id = currency.value
    if (dateFrom.value) params.date_from = dateFrom.value
    if (dateTo.value) params.date_to = dateTo.value
    if (eqType.value) params.equipment_type_id = eqType.value
    if (brand.value) params.brand_id = brand.value
    if (currentOnly.value) params.is_current = true
    const r = await priceApi.listPrices(params)
    items.value = r.data.data || []
  } finally { loading.value = false }
}

onMounted(load)
</script>

<style scoped>
.fl{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;align-items:center}
.fi{padding:5px 8px;border:1px solid #d1d5db;border-radius:5px;font-size:13px}
.cb{font-size:13px;display:flex;align-items:center;gap:4px}
.tb{width:100%;border-collapse:collapse;font-size:13px}
.tb th{text-align:left;padding:6px 10px;background:#f9fafb;border-bottom:2px solid #e5e7eb;color:#6b7280;font-weight:500}
.tb td{padding:6px 10px;border-bottom:1px solid #f3f4f6}
.pr{text-align:right;font-weight:500}
.st{text-align:center;padding:40px;color:#6b7280}
</style>