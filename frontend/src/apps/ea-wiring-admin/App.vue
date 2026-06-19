<template>
  <div class="wiring-admin">
    <div class="toolbar">
      <h2>Сигналы управления, обр.связи и схемы БУ (ControlUnitWiring)</h2>
      <div class="spacer"></div>
      <input v-model="searchQuery" placeholder="Поиск по коду, названию, БУ..." class="search-input" />
      <button class="btn btn-add" @click="openCreate">➕ Новая схема</button>
      <span v-if="loading" class="spinner">⏳</span>
      <span v-if="msg" class="msg" :class="msgType">{{ msg }}</span>
    </div>

    <!-- Таблица -->
    <table class="data-table" v-if="filteredWirings.length">
      <thead>
        <tr>
          <th>Код</th>
          <th>Название</th>
          <th>БУ</th>
          <th>Напряжение</th>
          <th>Профиль</th>
          <th>Схема</th>
          <th>Обогрев</th>
          <th>Акт.</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="w in filteredWirings" :key="w.id">
          <td class="code">{{ w.code }}</td>
          <td>{{ w.name }}</td>
          <td>{{ w.control_unit?.name || '—' }}</td>
          <td>{{ w.power_supply?.name || '—' }}</td>
          <td>{{ w.signal_profile?.name || '—' }}</td>
          <td>
            <img v-if="w.wiring_diagram?.preview_url" :src="w.wiring_diagram.preview_url" class="thumb" @error="e => e.target.style.display='none'" />
            <span v-else>—</span>
          </td>
          <td>{{ w.heater_supply?.name || '—' }}</td>
          <td><span :class="['badge', w.is_active ? 'on' : 'off']">{{ w.is_active ? 'Да' : 'Нет' }}</span></td>
          <td class="actions">
            <button class="btn-sm" @click="openEdit(w)">✏️</button>
            <button class="btn-sm btn-copy" @click="copyWiring(w)">📋</button>
            <button class="btn-sm btn-del" @click="confirmDelete(w)">🗑</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else-if="!loading" class="empty">Нет записей. Создайте первую схему.</div>

    <!-- Модалка: создать / редактировать -->
    <div v-if="showModal" class="modal-overlay">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingId ? 'Редактировать' : 'Новая схема' }}</h3>
          <button class="btn-close" @click="closeModal">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-field">
            <label>Код *</label>
            <input v-model="form.code" class="field-input" placeholder="I38-STD-SEP" />
          </div>
          <div class="form-field">
            <label>Название *</label>
            <input v-model="form.name" class="field-input" placeholder="INT 380В станд. (обогрев отд.кабель)" />
          </div>
          <div class="form-field">
            <label>Описание</label>
            <textarea v-model="form.description" class="field-input" rows="2"></textarea>
          </div>
          <div class="form-row">
            <div class="form-field">
              <label>Блок управления *</label>
              <select v-model.number="form.control_unit_id" class="field-input">
                <option :value="null">— выберите —</option>
                <option v-for="cu in controlUnits" :key="cu.id" :value="cu.id">{{ cu.name }}</option>
              </select>
            </div>
            <div class="form-field">
              <label>Напряжение *</label>
              <select v-model.number="form.power_supply_id" class="field-input">
                <option :value="null">— выберите —</option>
                <option v-for="ps in powerSupplies" :key="ps.id" :value="ps.id">{{ ps.name }}</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-field">
              <label>Профиль сигналов *</label>
              <select v-model.number="form.signal_profile_id" class="field-input">
                <option :value="null">— выберите —</option>
                <option v-for="sp in signalProfiles" :key="sp.id" :value="sp.id">{{ sp.name }}</option>
              </select>
            </div>
          </div>
          <!-- Аккордеон: профиль сигналов -->
          <div v-if="selectedSignalProfile" class="accordion">
            <div class="accordion-header" @click="showProfileAccordion = !showProfileAccordion">
              <span>📋 Профиль сигналов: {{ selectedSignalProfile.name }}</span>
              <span class="accordion-arrow">{{ showProfileAccordion ? '▾' : '▸' }}</span>
            </div>
            <div v-if="showProfileAccordion" class="accordion-body">
              <p v-if="selectedSignalProfile.description" class="profile-desc">{{ selectedSignalProfile.description }}</p>
              <table class="profile-table" v-if="selectedSignalProfile.entries?.length">
                <thead><tr><th>Роль</th><th>Направление</th><th>Компонент</th></tr></thead>
                <tbody>
                  <tr v-for="(e, i) in selectedSignalProfile.entries" :key="i">
                    <td>{{ e.role }}</td>
                    <td><span :class="['dir-badge', e.direction]">{{ e.direction === 'input' ? 'Вход' : e.direction === 'output' ? 'Выход' : e.direction === 'bidirectional' ? 'Вход/Выход' : e.direction }}</span></td>
                    <td>{{ e.component }}</td>
                  </tr>
                </tbody>
              </table>
              <div v-else class="empty-entries">Нет записей в профиле</div>
            </div>
          </div>
          <div class="form-field">
            <label>Изображение схемы</label>
            <input v-model="schemaFilter" placeholder="Фильтр по ключевым словам..." class="field-input field-filter" />
            <select v-model.number="form.wiring_diagram_id" class="field-input">
              <option :value="null">— не выбрано —</option>
              <option v-for="img in filteredSchemaImages" :key="img.id" :value="img.id">{{ img.code || img.name }}</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-field">
              <label>Питание обогрева</label>
              <select v-model.number="form.heater_supply_id" class="field-input">
                <option :value="null">— не выбрано —</option>
                <option v-for="hs in heaterSupplies" :key="hs.id" :value="hs.id">{{ hs.name }}</option>
              </select>
            </div>
          </div>
          <!-- Превью выбранного изображения схемы -->
          <div v-if="selectedSchemaImage" class="schema-preview">
            <div class="form-row">
              <div class="form-field">
                <label>Название схемы</label>
                <input :value="selectedSchemaImage.name" readonly class="field-input readonly" @focus="$event.target.select()" />
              </div>
              <div class="form-field">
                <label>Код схемы</label>
                <input :value="selectedSchemaImage.code" readonly class="field-input readonly" @focus="$event.target.select()" />
              </div>
            </div>
            <div class="schema-thumb-wrap" v-if="selectedSchemaImage.preview_url">
              <img :src="selectedSchemaImage.preview_url" class="schema-thumb" @click="openSchemaLightbox" @error="e => e.target.style.display='none'" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-field">
              <label>Сортировка</label>
              <input v-model.number="form.sorting_order" type="number" class="field-input" />
            </div>
            <div class="form-field">
              <label class="checkbox-label">
                <input type="checkbox" v-model="form.is_active" /> Активно
              </label>
            </div>
          </div>
          <div v-if="formError" class="form-error">{{ formError }}</div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-cancel" @click="closeModal">Отмена</button>
          <button class="btn btn-save" @click="saveForm" :disabled="saving">
            {{ saving ? '⏳' : '💾' }} {{ editingId ? 'Сохранить' : 'Создать' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Модалка: подтверждение удаления -->
    <div v-if="deleteTarget" class="modal-overlay">
      <div class="modal modal-sm">
        <div class="modal-header"><h3>Удалить схему?</h3></div>
        <div class="modal-body">
          <p><strong>{{ deleteTarget.code }}</strong> — {{ deleteTarget.name }}</p>
          <p class="warn">Это действие нельзя отменить.</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-cancel" @click="deleteTarget=null">Отмена</button>
          <button class="btn btn-del" @click="doDelete" :disabled="saving">🗑 Удалить</button>
        </div>
      </div>
    </div>

    <!-- Просмотрщик изображений схем -->
    <div v-if="schemaViewerShow" class="schema-lightbox" @click="schemaViewerShow=false" @keydown.escape="schemaViewerShow=false">
      <div class="schema-lightbox-toolbar">
        <span class="schema-lightbox-title">{{ selectedSchemaImage?.name || 'Схема' }}</span>
        <button class="schema-lightbox-close" @click.stop="schemaViewerShow=false">&times;</button>
      </div>
      <div class="schema-lightbox-body">
        <img v-if="schemaLightboxSrc"
          :src="schemaLightboxSrc"
          :alt="selectedSchemaImage?.name"
          class="schema-lightbox-img"
          @error="onSchemaImgError" />
        <div v-if="schemaImgFailed" class="schema-lightbox-fallback">
          <p>Большое изображение недоступно</p>
          <a v-if="selectedSchemaImage?.preview_url" :href="selectedSchemaImage.preview_url" target="_blank">Открыть превью</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import api from './api.js'

const wirings = ref([])
const loading = ref(false)
const saving = ref(false)
const msg = ref('')
const msgType = ref('ok')
const showModal = ref(false)
const editingId = ref(null)
const deleteTarget = ref(null)
const formError = ref('')

const controlUnits = ref([])
const powerSupplies = ref([])
const signalProfiles = ref([])
const schemaImages = ref([])
const heaterSupplies = ref([])
const searchQuery = ref('')
const schemaFilter = ref('')

// UI state
const showProfileAccordion = ref(true)
const schemaViewerShow = ref(false)
const schemaImgFailed = ref(false)
const schemaLightboxSrc = ref(null)

// Computed
const selectedSignalProfile = computed(() => signalProfiles.value.find(p => p.id === form.signal_profile_id) || null)
const selectedSchemaImage = computed(() => schemaImages.value.find(img => img.id === form.wiring_diagram_id) || null)
const filteredSchemaImages = computed(() => {
  const q = schemaFilter.value.toLowerCase().trim()
  if (!q) return schemaImages.value
  return schemaImages.value.filter(img =>
    (img.code || '').toLowerCase().includes(q) ||
    (img.name || '').toLowerCase().includes(q)
  )
})
const filteredWirings = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) return wirings.value
  return wirings.value.filter(w =>
    (w.code || '').toLowerCase().includes(q) ||
    (w.name || '').toLowerCase().includes(q) ||
    (w.control_unit?.name || '').toLowerCase().includes(q) ||
    (w.power_supply?.name || '').toLowerCase().includes(q) ||
    (w.signal_profile?.name || '').toLowerCase().includes(q) ||
    (w.heater_supply?.name || '').toLowerCase().includes(q) ||
    (w.wiring_diagram?.code || '').toLowerCase().includes(q) ||
    (w.wiring_diagram?.name || '').toLowerCase().includes(q)
  )
})
const emptyForm = () => ({
  code: '', name: '', description: '',
  control_unit_id: null, power_supply_id: null,
  signal_profile_id: null, wiring_diagram_id: null, heater_supply_id: null,
  is_active: true, sorting_order: 0,
})
const form = reactive(emptyForm())

async function fetchAll() {
  loading.value = true
  try {
    wirings.value = await api.list()
    msg.value = ''
  } catch (e) { msg.value = 'Ошибка загрузки'; msgType.value = 'err' }
  finally { loading.value = false }
}

async function loadRefs() {
  try {
    const r = await fetch('/api/electric_actuators/admin/wirings/refs/').then(r => r.json())
    controlUnits.value = r.control_units || []
    powerSupplies.value = r.power_supplies || []
    signalProfiles.value = r.signal_profiles || []
    schemaImages.value = r.schema_images || []
    heaterSupplies.value = r.heater_supplies || []
  } catch (e) { /* не критично */ }
}

function openCreate() {
  Object.assign(form, emptyForm())
  editingId.value = null
  formError.value = ''
  schemaFilter.value = ''
  showModal.value = true
}

function openEdit(w) {
  editingId.value = w.id
  Object.assign(form, {
    code: w.code,
    name: w.name,
    description: w.description || '',
    control_unit_id: w.control_unit?.id || null,
    power_supply_id: w.power_supply?.id || null,
    signal_profile_id: w.signal_profile?.id || null,
    wiring_diagram_id: w.wiring_diagram?.id || null,
    heater_supply_id: w.heater_supply?.id || null,
    is_active: w.is_active,
    sorting_order: w.sorting_order,
  })
  formError.value = ''
  schemaFilter.value = ''
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingId.value = null
}

async function saveForm() {
  if (!form.code || !form.name || !form.control_unit_id || !form.power_supply_id || !form.signal_profile_id) {
    formError.value = 'Заполните обязательные поля: код, название, БУ, напряжение, профиль'
    return
  }
  saving.value = true; formError.value = ''
  const payload = { ...form }
  try {
    if (editingId.value) {
      await api.update(editingId.value, payload)
    } else {
      await api.create(payload)
    }
    closeModal()
    await fetchAll()
  } catch (e) {
    formError.value = 'Ошибка: ' + (e.response?.data?.errors || e.response?.data?.error || e.message)
  }
  finally { saving.value = false }
}

function confirmDelete(w) {
  deleteTarget.value = w
}

async function doDelete() {
  if (!deleteTarget.value) return
  saving.value = true
  try {
    await api.remove(deleteTarget.value.id)
    deleteTarget.value = null
    await fetchAll()
  } catch (e) {
    msg.value = 'Ошибка удаления: ' + (e.response?.data?.error || e.message); msgType.value = 'err'
    deleteTarget.value = null
  }
  finally { saving.value = false }
}

async function copyWiring(w) {
  saving.value = true; msg.value = ''
  try {
    await api.copy(w.id)
    await fetchAll()
    msg.value = 'Копия создана'; msgType.value = 'ok'
  } catch (e) {
    msg.value = 'Ошибка копирования: ' + (e.response?.data?.error || e.message); msgType.value = 'err'
  }
  finally { saving.value = false }
}

function openSchemaLightbox() {
  const img = selectedSchemaImage.value
  if (!img) return
  schemaImgFailed.value = false
  // full_url (svg/full) в приоритете, иначе preview_url
  schemaLightboxSrc.value = img.full_url || img.preview_url || null
  schemaViewerShow.value = true
}

function onSchemaImgError() {
  const img = selectedSchemaImage.value
  // fallback: если full_url не загрузился, пробуем preview_url
  if (schemaLightboxSrc.value && schemaLightboxSrc.value !== img?.preview_url && img?.preview_url) {
    schemaLightboxSrc.value = img.preview_url
    return
  }
  schemaImgFailed.value = true
}

// Автозаполнение кода при выборе схемы (только при создании)
watch(() => form.wiring_diagram_id, (newId) => {
  if (!newId) return
  // Не перезаписываем, если код уже задан вручную
  if (form.code && form.code.trim()) return
  const img = schemaImages.value.find(i => i.id === newId)
  if (img?.code) form.code = img.code
})

onMounted(() => { fetchAll(); loadRefs() })
</script>

<style scoped>
.wiring-admin { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 14px; color: #1a1a2e; background: #f0f2f5; min-height: 100vh; padding: 16px 24px; }
.toolbar { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.toolbar h2 { margin: 0; font-size: 18px; }
.spacer { flex: 1; }
.search-input { padding: 6px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; width: 240px; }
.search-input:focus { border-color: #1976d2; outline: none; }
.spinner { font-size: 18px; }
.msg { font-size: 13px; padding: 4px 10px; border-radius: 4px; }
.msg.ok { background: #e6ffe6; color: #2e7d32; }
.msg.err { background: #ffe6e6; color: #c62828; }
.btn { padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; }
.btn-add { background: #1976d2; color: #fff; }
.btn-save { background: #1976d2; color: #fff; }
.btn-save:disabled { opacity: 0.5; cursor: default; }
.btn-cancel { background: #eee; color: #333; }
.btn-del { background: #c62828; color: #fff; }
.btn-sm { padding: 4px 8px; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; background: #eee; }
.btn-sm:hover { background: #ddd; }
.btn-sm.btn-del:hover { background: #ef5350; color: #fff; }
.btn-sm.btn-copy { background: #e8f5e9; color: #2e7d32; }
.btn-sm.btn-copy:hover { background: #c8e6c9; }


.data-table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.1); }
.data-table th { background: #f5f5f5; padding: 10px 12px; text-align: left; font-size: 12px; text-transform: uppercase; color: #666; border-bottom: 2px solid #e0e0e0; }
.data-table td { padding: 8px 12px; border-bottom: 1px solid #f0f0f0; }
.data-table tr:hover td { background: #f8f9fb; }
.code { font-weight: 600; font-family: monospace; }
.badge { font-size: 11px; padding: 2px 8px; border-radius: 10px; }
.badge.on { background: #e8f5e9; color: #2e7d32; }
.badge.off { background: #f5f5f5; color: #999; }
.thumb { max-height: 40px; max-width: 60px; border-radius: 4px; border: 1px solid #ddd; }
.actions { white-space: nowrap; }
.empty { text-align: center; padding: 40px; color: #999; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: #fff; border-radius: 10px; width: 560px; max-height: 90vh; overflow-y: auto; box-shadow: 0 8px 32px rgba(0,0,0,.2); }
.modal-sm { width: 400px; }
.modal-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; border-bottom: 1px solid #e0e0e0; }
.modal-header h3 { margin: 0; font-size: 16px; }
.btn-close { background: none; border: none; font-size: 18px; cursor: pointer; color: #999; }
.modal-body { padding: 16px 20px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 8px; padding: 12px 20px; border-top: 1px solid #e0e0e0; }

.form-field { margin-bottom: 10px; display: flex; flex-direction: column; }
.form-field label { font-size: 12px; color: #666; margin-bottom: 3px; font-weight: 500; }
.field-input { padding: 6px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; }
.field-input:focus { border-color: #1976d2; outline: none; }
.field-filter { margin-bottom: 4px; font-size: 12px; }
.form-row { display: flex; gap: 10px; }
.form-row .form-field { flex: 1; }
.checkbox-label { display: flex; align-items: center; gap: 6px; cursor: pointer; padding-top: 18px; }
.form-error { color: #c62828; font-size: 13px; margin-top: 8px; padding: 6px 10px; background: #ffe6e6; border-radius: 4px; }
.warn { color: #c62828; font-size: 13px; }

/* Аккордеон профиля сигналов */
.accordion { margin-top: 8px; border: 1px solid #e0e0e0; border-radius: 6px; overflow: hidden; }
.accordion-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: #f5f5f5; cursor: pointer; font-size: 13px; font-weight: 500; user-select: none; }
.accordion-header:hover { background: #eee; }
.accordion-arrow { font-size: 12px; color: #999; }
.accordion-body { padding: 10px 12px; background: #fff; }
.profile-desc { font-size: 12px; color: #666; margin: 0 0 8px; }
.profile-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.profile-table th { text-align: left; padding: 4px 8px; background: #f9fafb; color: #666; font-weight: 500; border-bottom: 1px solid #e0e0e0; }
.profile-table td { padding: 4px 8px; border-bottom: 1px solid #f0f0f0; }
.dir-badge { font-size: 10px; padding: 1px 6px; border-radius: 8px; }
.dir-badge.input { background: #e3f2fd; color: #1565c0; }
.dir-badge.output { background: #e8f5e9; color: #2e7d32; }
.dir-badge.bidirectional { background: #f3e5f5; color: #7b1fa2; }
.empty-entries { font-size: 12px; color: #999; padding: 4px 0; }

/* Превью схемы */
.schema-preview { margin-top: 10px; padding: 10px; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; }
.field-input.readonly { background: #f9fafb; color: #555; cursor: text; user-select: text; }
.schema-thumb-wrap { margin-top: 8px; text-align: center; }
.schema-thumb { max-height: 120px; max-width: 100%; border-radius: 4px; border: 1px solid #ddd; cursor: pointer; transition: box-shadow 0.15s; }
.schema-thumb:hover { box-shadow: 0 0 0 2px #1976d2; }

/* Лайтбокс схемы (быстрый, без iframe) */
.schema-lightbox { position: fixed; inset: 0; z-index: 2000; background: rgba(0,0,0,0.92); display: flex; flex-direction: column; }
.schema-lightbox-toolbar { display: flex; align-items: center; gap: 12px; padding: 10px 16px; background: rgba(0,0,0,0.5); color: #fff; font-size: 14px; flex-shrink: 0; }
.schema-lightbox-title { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.schema-lightbox-close { background: none; border: none; color: #fff; font-size: 28px; cursor: pointer; padding: 0 4px; line-height: 1; }
.schema-lightbox-body { flex: 1; display: flex; align-items: center; justify-content: center; padding: 40px; overflow: auto; }
.schema-lightbox-img { max-width: 100%; max-height: 100%; object-fit: contain; }
.schema-lightbox-fallback { text-align: center; color: #fff; }
.schema-lightbox-fallback p { margin: 0 0 12px; font-size: 15px; }
.schema-lightbox-fallback a { color: #64b5f6; font-size: 14px; }
</style>