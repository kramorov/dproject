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

      <!-- Основное -->
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

      <!-- Кнопка "Заполнить из модели" -->
      <div class="wa-form-group">
        <button class="wa-btn-secondary" @click="fillFromModel" :disabled="!form.equipment_type_id || !equipmentTypeContentTypeId">
          📋 Заполнить фильтры из модели
        </button>
      </div>

      <!-- Страницы -->
      <h3>Страницы (шаги)</h3>
      <div class="wa-subsection">
        <div v-for="(page, pi) in form.pages" :key="pi" class="wa-card">
          <div class="wa-card-header">
            <strong>Шаг {{ page.step_number || (pi + 1) }}</strong>
            <button class="wa-btn-danger" @click="form.pages.splice(pi, 1)">✕</button>
          </div>
          <div class="wa-form-row">
            <label>Номер шага</label>
            <input v-model.number="page.step_number" type="number" class="wa-input-sm" />
          </div>
          <div class="wa-form-row">
            <label>Заголовок</label>
            <input v-model="page.title" class="wa-input" />
          </div>
          <div class="wa-form-row">
            <label>Описание</label>
            <textarea v-model="page.description" class="wa-textarea" rows="2"></textarea>
          </div>
        </div>
        <button class="wa-btn-secondary" @click="addPage">+ Добавить шаг</button>
      </div>

      <!-- Фильтры -->
      <h3>Фильтры</h3>
      <div class="wa-subsection">
        <div v-for="(filter, fi) in form.filters" :key="fi" class="wa-card">
          <div class="wa-card-header">
            <strong>{{ filter.param_name || 'новый фильтр' }}</strong>
            <button class="wa-btn-danger" @click="form.filters.splice(fi, 1)">✕</button>
          </div>
          <div class="wa-form-row">
            <label>param_name</label>
            <select v-model="filter.param_name" class="wa-input">
              <option value="">— выберите —</option>
              <option v-for="mf in modelFilters" :key="mf.param_name" :value="mf.param_name">{{ mf.label }} ({{ mf.param_name }})</option>
            </select>
          </div>
          <div class="wa-form-row">
            <label>Страница (шаг)</label>
            <select v-model.number="filter.page" class="wa-input-sm">
              <option v-for="p in form.pages" :key="p.step_number || 0" :value="p.step_number || 0">
                Шаг {{ p.step_number || '?' }}: {{ p.title || 'без названия' }}
              </option>
            </select>
          </div>
          <div class="wa-form-row">
            <label>Порядок</label>
            <input v-model.number="filter.order" type="number" class="wa-input-sm" />
          </div>
          <div class="wa-form-row">
            <label>Заголовок фильтра</label>
            <input v-model="filter.label" class="wa-input" />
          </div>
          <div class="wa-form-row">
            <label>Значение по умолчанию</label>
            <input v-model="filter.default_value" class="wa-input-sm" placeholder="null" />
          </div>
        </div>
        <button class="wa-btn-secondary" @click="addFilter">+ Добавить фильтр</button>
      </div>

      <!-- Кнопки сохранения -->
      <div class="wa-actions">
        <button class="wa-btn-primary" @click="saveWizard" :disabled="saving">{{ saving ? 'Сохранение...' : '💾 Сохранить' }}</button>
        <button class="wa-btn-secondary" @click="cancelEdit">Отмена</button>
      </div>

      <div v-if="saveError" class="wa-error">{{ saveError }}</div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/shared/api'

// ── Данные ──
const wizards = ref([])
const equipmentTypes = ref([])
const modelFilters = ref([])
const equipmentTypeContentTypeId = ref(null)
const editing = ref(false)
const isNew = ref(true)
const saving = ref(false)
const saveError = ref('')


const form = reactive({
  id: null,
  name: '',
  code: '',
  equipment_type_id: null,
  is_active: true,
  pages: [],
  filters: [],
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
}

function editWizard(w) {
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

  // Загружаем информацию о модели
  if (form.equipment_type_id) {
    loadContentTypeForET(form.equipment_type_id)
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

async function fillFromModel() {
  if (!equipmentTypeContentTypeId.value) return
  try {
    const { data } = await api.get('/core/wizard/model-filters/', {
      params: { content_type_id: equipmentTypeContentTypeId.value }
    })
    modelFilters.value = data.filters || []

    // Авто-заполняем filters из модели
    const filters = (data.filters || []).map((mf, i) => ({
      param_name: mf.param_name,
      page: form.pages[0]?.step_number || 1,
      order: i + 1,
      label: mf.label,
      default_value: mf.default_value || null,
    }))
    form.filters = filters
  } catch (e) {
    console.error('Failed to fill from model:', e)
  }
}

function addPage() {
  const maxNum = form.pages.reduce((m, p) => Math.max(m, p.step_number || 0), 0)
  form.pages.push({ step_number: maxNum + 1, title: '', description: '' })
}

function addFilter() {
  form.filters.push({
    param_name: '',
    page: form.pages[0]?.step_number || 1,
    order: form.filters.length + 1,
    label: '',
    default_value: null,
  })
}

async function saveWizard() {
  saving.value = true
  saveError.value = ''

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

.wa-section { margin-bottom: 32px; }
.wa-subsection { margin-left: 8px; }

.wa-table { width: 100%; border-collapse: collapse; margin-bottom: 12px; }
.wa-table th, .wa-table td { text-align: left; padding: 8px 12px; border-bottom: 1px solid #e5e7eb; font-size: 13px; }
.wa-table th { font-weight: 600; color: #6b7280; }
.wa-table button { margin-right: 4px; font-size: 12px; padding: 2px 8px; cursor: pointer; }

.wa-empty { padding: 24px; color: #9ca3af; font-size: 14px; }

.wa-form-group { margin-bottom: 12px; }
.wa-form-group label { display: block; font-size: 13px; font-weight: 500; margin-bottom: 4px; color: #374151; }
.wa-form-row { display: flex; gap: 12px; align-items: center; margin-bottom: 8px; }
.wa-form-row label { font-size: 12px; color: #6b7280; min-width: 140px; }

.wa-input { width: 100%; padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px; }
.wa-input-sm { padding: 4px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px; width: 120px; }
.wa-textarea { width: 100%; padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px; resize: vertical; }

.wa-card { border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; margin-bottom: 10px; background: #f9fafb; }
.wa-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.wa-card-header strong { font-size: 14px; }

.wa-actions { display: flex; gap: 8px; margin-top: 20px; }

.wa-btn-primary { padding: 8px 20px; background: #2563eb; color: #fff; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; }
.wa-btn-primary:disabled { opacity: .5; cursor: default; }
.wa-btn-secondary { padding: 6px 16px; background: #fff; color: #374151; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px; cursor: pointer; }
.wa-btn-secondary:disabled { opacity: .5; cursor: default; }
.wa-btn-danger { padding: 2px 8px; background: #fff; color: #ef4444; border: 1px solid #fca5a5; border-radius: 4px; font-size: 12px; cursor: pointer; }

.wa-error { margin-top: 12px; padding: 8px 16px; background: #fef2f2; color: #dc2626; border-radius: 6px; font-size: 13px; }

</style>
