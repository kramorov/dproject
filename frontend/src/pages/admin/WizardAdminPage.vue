<!-- pages/admin/WizardAdminPage.vue — Админка мастера подбора -->
<template>
  <div class="wizard-admin">
    <h1>Мастер подбора</h1>

    <!-- Список существующих -->
    <section class="wa-section">
      <h2>Существующие мастера</h2>
      <table class="wa-table" v-if="wizards.length">
        <thead><tr><th>ID</th><th>Название</th><th>Тип оборудования</th><th>Активен</th><th></th></tr></thead>
        <tbody>
          <tr v-for="w in wizards" :key="w.id">
            <td>{{ w.id }}</td>
            <td>{{ w.name }}</td>
            <td>{{ w.equipment_type_name || '-' }}</td>
            <td>{{ w.is_active ? '✓' : '—' }}</td>
            <td><button @click="editWizard(w)">Ред.</button><button @click="deleteWizard(w.id)" class="wa-btn-danger">Уд.</button></td>
          </tr>
        </tbody>
      </table>
      <div v-else class="wa-empty">Нет мастеров. Создайте новый.</div>
      <button class="wa-btn-primary" @click="newWizard">+ Новый мастер</button>
    </section>

    <!-- Редактор -->
    <section class="wa-section" v-if="editing">
      <h2>{{ isNew ? 'Новый мастер' : 'Редактирование' }}</h2>

      <div class="wa-form-group">
        <label>Название</label>
        <input v-model="form.name" class="wa-input" />
      </div>
      <div class="wa-form-group">
        <label>Код</label>
        <input v-model="form.code" class="wa-input" />
      </div>
      <div class="wa-form-group">
        <label>Тип оборудования</label>
        <select v-model="form.equipment_type_id" class="wa-input" @change="onEquipmentTypeChange">
          <option :value="null">— выберите —</option>
          <option v-for="et in equipmentTypes" :key="et.id" :value="et.id">{{ et.name }} (ID: {{ et.id }})</option>
        </select>
      </div>
      <div class="wa-form-group">
        <label><input type="checkbox" v-model="form.is_active" /> Активен</label>
      </div>

      <div class="wa-form-group">
        <button class="wa-btn-secondary" @click="fillFromModel" :disabled="!form.equipment_type_id || !equipmentTypeContentTypeId">
          📋 Заполнить фильтры из модели
        </button>
      </div>

      <!-- ═══ Табы шагов ═══ -->
      <h3>Шаги</h3>
      <div class="wa-tabs">
        <button
          v-for="(page, pi) in form.pages" :key="pi"
          class="wa-tab"
          :class="{ active: activePageTab === pi }"
          @click="activePageTab = pi; activeFilterTab = 0"
        >
          Шаг {{ page.step_number || pi + 1 }}
        </button>
        <button class="wa-tab wa-tab-add" @click="addPage">+</button>
      </div>

      <!-- Содержимое активного шага -->
      <div v-if="form.pages[activePageTab]" class="wa-tab-content">
        <div class="wa-card">
          <div class="wa-card-header">
            <strong>Шаг {{ form.pages[activePageTab].step_number || activePageTab + 1 }}</strong>
            <button class="wa-btn-danger" @click="removePage(activePageTab)">✕ Удалить шаг</button>
          </div>
          <div class="wa-form-row">
            <label>Номер шага</label>
            <input v-model.number="form.pages[activePageTab].step_number" type="number" class="wa-input-sm" />
          </div>
          <div class="wa-form-row">
            <label>Заголовок</label>
            <input v-model="form.pages[activePageTab].title" class="wa-input" />
          </div>
          <div class="wa-form-row">
            <label>Описание</label>
            <textarea v-model="form.pages[activePageTab].description" class="wa-textarea" rows="2"></textarea>
          </div>
        </div>

        <!-- ═══ Табы фильтров шага ═══ -->
        <h4>Фильтры этого шага</h4>
        <div class="wa-tabs wa-tabs-sm" v-if="pageFilters.length">
          <button
            v-for="(f, fi) in pageFilters" :key="fi"
            class="wa-tab"
            :class="{ active: activeFilterTab === fi }"
            @click="activeFilterTab = fi"
          >
            {{ f.param_name || f.label || 'новый' }}
          </button>
        </div>
        <div v-else class="wa-empty-sm">Нет фильтров на этом шаге.</div>
        <button class="wa-btn-secondary wa-btn-sm" @click="addFilterToPage(form.pages[activePageTab])">+ Добавить фильтр</button>

        <!-- Карточка активного фильтра -->
        <div v-if="pageFilters[activeFilterTab]" class="wa-card wa-filter-card">
          <div class="wa-filter-row">
            <select v-model="pageFilters[activeFilterTab].param_name" class="wa-input" @change="onFilterParamChange(pageFilters[activeFilterTab].param_name)">
              <option value="">— param_name —</option>
              <option v-for="mf in modelFilters" :key="mf.param_name" :value="mf.param_name">
                {{ mf.label }} ({{ mf.param_name }})
              </option>
            </select>
            <select v-model.number="pageFilters[activeFilterTab].page" class="wa-input-sm">
              <option v-for="p in form.pages" :key="p.step_number" :value="p.step_number">
                Шаг {{ p.step_number }}
              </option>
            </select>
            <label class="wa-inline-label">Порядок</label>
            <input v-model.number="pageFilters[activeFilterTab].order" type="number" class="wa-input-xs" />
            <button class="wa-btn-danger" @click="removeFilter(activeFilterTab)">✕</button>
          </div>
          <div class="wa-form-row">
            <label>Заголовок</label>
            <input v-model="pageFilters[activeFilterTab].label" class="wa-input" />
          </div>
          <div class="wa-form-row">
            <label>Значение по умолчанию</label>
            <select
              v-if="pageFilters[activeFilterTab].param_name && filterOptionValues[pageFilters[activeFilterTab].param_name]?.length"
              v-model="pageFilters[activeFilterTab].default_value"
              class="wa-input-sm"
              style="width:200px"
            >
              <option :value="null">— не выбрано —</option>
              <option
                v-for="opt in filterOptionValues[pageFilters[activeFilterTab].param_name] || []"
                :key="opt.id ?? opt.value"
                :value="opt.id ?? opt.value"
              >{{ opt.name }}{{ opt.code ? ' (' + opt.code + ')' : '' }}</option>
            </select>
            <input
              v-else
              v-model="pageFilters[activeFilterTab].default_value"
              class="wa-input-sm"
              placeholder="null"
            />
          </div>
        </div>
      </div>

      <div class="wa-actions">
        <button class="wa-btn-primary" @click="saveWizard" :disabled="saving">{{ saving ? 'Сохранение...' : '💾 Сохранить' }}</button>
        <button class="wa-btn-secondary" @click="cancelEdit">Отмена</button>
      </div>

      <div v-if="saveError" class="wa-error">{{ saveError }}</div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import api from '@/shared/api'

const wizards = ref([])
const equipmentTypes = ref([])
const modelFilters = ref([])
const equipmentTypeContentTypeId = ref(null)
const editing = ref(false)
const isNew = ref(true)
const saving = ref(false)
const saveError = ref('')
const activePageTab = ref(0)
const activeFilterTab = ref(0)
const filterOptionValues = ref({})  // { param_name: [{id, name}, ...] }

const form = reactive({
  id: null,
  name: '',
  code: '',
  equipment_type_id: null,
  is_active: true,
  pages: [],
  filters: [],
})

// ── Фильтры текущего шага, отсортированные по order ──
const pageFilters = computed(() => {
  const page = form.pages[activePageTab.value]
  if (!page) return []
  const stepNum = page.step_number
  return form.filters
    .filter(f => f.page === stepNum)
    .sort((a, b) => (a.order || 0) - (b.order || 0))
})

// ── Загрузка ──
onMounted(async () => {
  await loadWizards()
  await loadEquipmentTypes()
})

async function loadWizards() {
  try {
    const { data } = await api.get('/core/wizard/admin/')
    wizards.value = (data.data || []).map(w => ({
      ...w,
      equipment_type_name: w.equipment_type_name || '-'
    }))
  } catch (e) {
    console.error('Failed to load wizards:', e)
  }
}

async function loadEquipmentTypes() {
  try {
    const { data } = await api.get('/core/wizard/model-filters/equipment-types/')
    equipmentTypes.value = (data.data || [])
  } catch (e) {
    console.error('Failed to load equipment types:', e)
  }
}

// ── Действия ──
function newWizard() {
  form.id = null
  form.name = ''
  form.code = ''
  form.equipment_type_id = null
  form.is_active = true
  form.pages = [{ step_number: 1, title: '', description: '' }]
  form.filters = []
  modelFilters.value = []
  equipmentTypeContentTypeId.value = null
  isNew.value = true
  editing.value = true
  saveError.value = ''
  activePageTab.value = 0
  activeFilterTab.value = 0
}

async function editWizard(w) {
  form.id = w.id
  form.name = w.name || ''
  form.code = w.code || ''
  form.equipment_type_id = w.equipment_type_id
  form.is_active = w.is_active !== false

  const json = w.steps_json || {}
  form.pages = json.pages || []
  form.filters = json.filters || []

  isNew.value = false
  editing.value = true
  saveError.value = ''
  activePageTab.value = 0
  activeFilterTab.value = 0

  if (form.equipment_type_id) {
    await loadContentTypeForET(form.equipment_type_id)
    await loadModelFiltersForEditor()
  }
}

function cancelEdit() {
  editing.value = false
  saveError.value = ''
}

async function onEquipmentTypeChange() {
  modelFilters.value = []
  equipmentTypeContentTypeId.value = null
  if (form.equipment_type_id) {
    await loadContentTypeForET(form.equipment_type_id)
  }
}

async function loadContentTypeForET(etId) {
  try {
    const { data } = await api.get(`/core/wizard/model-filters/equipment-types/${etId}/`)
    const ctId = data?.content_type_id
    if (ctId) {
      equipmentTypeContentTypeId.value = ctId
    }
  } catch (e) {
    console.error('Failed to load content type:', e)
  }
}

async function loadModelFiltersForEditor() {
  if (!equipmentTypeContentTypeId.value) return
  try {
    const { data } = await api.get('/core/wizard/model-filters/', {
      params: { content_type_id: equipmentTypeContentTypeId.value }
    })
    modelFilters.value = data.filters || []
    // Load option values for all existing filter param_names
    for (const f of form.filters) {
      if (f.param_name && !filterOptionValues.value[f.param_name]) {
        await loadFilterOptions(f.param_name)
      }
    }
  } catch (e) {
    console.error('Failed to load model filters:', e)
  }
}

async function loadFilterOptions(paramName) {
  if (!paramName || !form.equipment_type_id) return
  try {
    const { data } = await api.post(`/core/wizard/${form.equipment_type_id}/filter-options/`, {
      param_name: paramName,
      filters_applied: {},
    })
    filterOptionValues.value[paramName] = data.options || []
  } catch (e) {
    console.error('Failed to load filter options for', paramName, e)
  }
}

async function onFilterParamChange(paramName) {
  if (paramName && !filterOptionValues.value[paramName]) {
    await loadFilterOptions(paramName)
  }
}

async function fillFromModel() {
  if (!equipmentTypeContentTypeId.value) return
  try {
    const { data } = await api.get('/core/wizard/model-filters/', {
      params: { content_type_id: equipmentTypeContentTypeId.value }
    })
    modelFilters.value = data.filters || []

    const filters = (data.filters || []).map((mf, i) => ({
      param_name: mf.param_name,
      page: form.pages[0]?.step_number || 1,
      order: i + 1,
      label: mf.label,
      default_value: mf.default_value || null,
    }))
    form.filters = filters
    activeFilterTab.value = 0
  } catch (e) {
    console.error('Failed to fill from model:', e)
  }
}

function addPage() {
  const maxNum = form.pages.reduce((m, p) => Math.max(m, p.step_number || 0), 0)
  form.pages.push({ step_number: maxNum + 1, title: '', description: '' })
  activePageTab.value = form.pages.length - 1
  activeFilterTab.value = 0
}

function removePage(index) {
  if (form.pages.length <= 1) return
  form.pages.splice(index, 1)
  if (activePageTab.value >= form.pages.length) {
    activePageTab.value = form.pages.length - 1
  }
  activeFilterTab.value = 0
}

function addFilterToPage(page) {
  const existing = form.filters.filter(f => f.page === page.step_number)
  const maxOrder = existing.reduce((m, f) => Math.max(m, f.order || 0), 0)
  form.filters.push({
    param_name: '',
    page: page.step_number,
    order: maxOrder + 1,
    label: '',
    default_value: null,
  })
  // Switch to the new filter
  activeFilterTab.value = pageFilters.value.length - 1
}

function removeFilter(index) {
  const pf = pageFilters.value
  if (!pf[index]) return
  const target = pf[index]
  const globalIndex = form.filters.findIndex(
    f => f.param_name === target.param_name && f.page === target.page && f.order === target.order
  )
  if (globalIndex >= 0) {
    form.filters.splice(globalIndex, 1)
  }
  if (activeFilterTab.value >= pf.length - 1 && activeFilterTab.value > 0) {
    activeFilterTab.value = Math.max(0, pf.length - 2)
  }
}

// ── Валидация ──
function validate() {
  // 1. Уникальность номеров страниц
  const pageNums = form.pages.map(p => p.step_number)
  const seen = new Set()
  for (const n of pageNums) {
    if (n === null || n === undefined || n === '') continue
    if (seen.has(n)) return `Номера шагов должны быть уникальны — шаг ${n} повторяется`
    seen.add(n)
  }

  // 2. Все фильтры ссылаются на существующие страницы
  for (const f of form.filters) {
    if (f.page === null || f.page === undefined) continue
    if (!pageNums.includes(f.page)) {
      return `Фильтр «${f.param_name || f.label || 'без названия'}» ссылается на несуществующий шаг ${f.page}`
    }
  }

  // 3. Уникальность порядка фильтров в пределах одного шага
  const pageOrders = {}
  for (const f of form.filters) {
    if (f.page == null || f.order == null) continue
    if (!pageOrders[f.page]) pageOrders[f.page] = new Set()
    if (pageOrders[f.page].has(f.order)) {
      return `На шаге ${f.page} есть несколько фильтров с порядком ${f.order}`
    }
    pageOrders[f.page].add(f.order)
  }

  return null
}

async function saveWizard() {
  saving.value = true
  saveError.value = ''

  const err = validate()
  if (err) {
    saveError.value = err
    saving.value = false
    return
  }

  const payload = {
    name: form.name,
    code: form.code || null,
    equipment_type_id: form.equipment_type_id,
    is_active: form.is_active,
    steps_json: {
      pages: form.pages,
      filters: form.filters.map(f => ({
        ...f,
        default_value: f.default_value === '' || f.default_value === 'null' ? null : f.default_value
      }))
    },
  }

  try {
    if (isNew.value) {
      await api.post('/core/wizard/admin/', payload)
    } else {
      await api.put(`/core/wizard/admin/${form.id}/`, payload)
    }
    editing.value = false
    await loadWizards()
  } catch (e) {
    saveError.value = e.response?.data?.error || 'Ошибка сохранения'
    console.error('Save error:', e)
  } finally {
    saving.value = false
  }
}

async function deleteWizard(id) {
  if (!confirm('Удалить мастера подбора?')) return
  try {
    await api.delete(`/core/wizard/admin/${id}/`)
    await loadWizards()
  } catch (e) {
    console.error('Delete error:', e)
  }
}
</script>

<style scoped>
.wizard-admin {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 16px;
  font-family: system-ui, sans-serif;
  color: #1f2937;
}
h1 { font-size: 24px; margin: 0 0 24px; }
h2 { font-size: 18px; margin: 0 0 16px; }
h3 { font-size: 16px; margin: 24px 0 12px; border-bottom: 1px solid #e5e7eb; padding-bottom: 8px; }
h4 { font-size: 14px; margin: 16px 0 8px; color: #6b7280; }

.wa-section { margin-bottom: 32px; }

.wa-table { width: 100%; border-collapse: collapse; margin-bottom: 12px; }
.wa-table th, .wa-table td { text-align: left; padding: 8px 12px; border-bottom: 1px solid #e5e7eb; font-size: 13px; }
.wa-table th { font-weight: 600; color: #6b7280; }
.wa-table button { margin-right: 4px; font-size: 12px; padding: 2px 8px; cursor: pointer; }

.wa-empty { padding: 24px; color: #9ca3af; font-size: 14px; }
.wa-empty-sm { padding: 8px 0; color: #9ca3af; font-size: 13px; }

.wa-form-group { margin-bottom: 12px; }
.wa-form-group label { display: block; font-size: 13px; font-weight: 500; margin-bottom: 4px; color: #374151; }
.wa-form-row { display: flex; gap: 12px; align-items: center; margin-bottom: 8px; }
.wa-form-row label { font-size: 12px; color: #6b7280; min-width: 100px; }

.wa-input { width: 100%; padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px; }
.wa-input-sm { padding: 4px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px; width: 100px; }
.wa-input-xs { padding: 4px 6px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px; width: 60px; }
.wa-textarea { width: 100%; padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px; resize: vertical; }

/* Tabs */
.wa-tabs { display: flex; gap: 4px; margin-bottom: 12px; flex-wrap: wrap; }
.wa-tabs-sm { gap: 2px; }
.wa-tab { padding: 6px 14px; border: 1px solid #d1d5db; border-radius: 6px 6px 0 0; background: #f3f4f6; font-size: 13px; cursor: pointer; color: #6b7280; border-bottom: none; }
.wa-tab.active { background: #fff; color: #1f2937; font-weight: 600; border-bottom: 2px solid #2563eb; }
.wa-tab:hover:not(.active) { background: #e5e7eb; }
.wa-tab-add { border-radius: 6px; padding: 6px 10px; font-weight: bold; }

.wa-tab-content { border: 1px solid #e5e7eb; border-radius: 0 6px 6px 6px; padding: 16px; background: #fff; margin-bottom: 16px; }

/* Card */
.wa-card { border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; margin-bottom: 10px; background: #f9fafb; }
.wa-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.wa-card-header strong { font-size: 14px; }
.wa-filter-card { margin-top: 10px; }

/* Filter row — всё в одну строку */
.wa-filter-row { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; flex-wrap: wrap; }
.wa-filter-row .wa-input { flex: 1; min-width: 160px; }
.wa-inline-label { font-size: 12px; color: #6b7280; white-space: nowrap; }

.wa-actions { display: flex; gap: 8px; margin-top: 20px; }

.wa-btn-primary { padding: 8px 20px; background: #2563eb; color: #fff; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; }
.wa-btn-primary:disabled { opacity: .5; cursor: default; }
.wa-btn-secondary { padding: 6px 16px; background: #fff; color: #374151; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; cursor: pointer; }
.wa-btn-secondary:disabled { opacity: .5; cursor: default; }
.wa-btn-sm { padding: 4px 10px; font-size: 12px; }
.wa-btn-danger { padding: 2px 8px; background: #fff; color: #ef4444; border: 1px solid #fca5a5; border-radius: 4px; font-size: 12px; cursor: pointer; }

.wa-error { margin-top: 12px; padding: 8px 16px; background: #fef2f2; color: #dc2626; border-radius: 6px; font-size: 13px; }
</style>
