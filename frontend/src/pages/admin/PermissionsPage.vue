<!-- pages/admin/PermissionsPage.vue — управление правами доступа -->
<template>
  <div class="perm-page">
    <h2>Управление правами доступа</h2>

    <!-- Табы -->
    <nav class="tabs">
      <button :class="{ active: tab === 'sections' }" @click="tab = 'sections'">Разделы</button>
      <button :class="{ active: tab === 'matrix' }" @click="tab = 'matrix'">Матрица прав</button>
    </nav>

    <!-- === TAB 1: SiteSections === -->
    <section v-if="tab === 'sections'" class="tab-panel">
      <table class="data-table" v-if="siteSections.length">
        <thead>
          <tr><th>Код</th><th>Название</th><th>Активен</th><th>Порядок</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="s in siteSections" :key="s.code" :class="{ inactive: !s.is_active }">
            <td><code>{{ s.code }}</code></td>
            <td>
              <template v-if="editingSection === s.code">
                <input v-model="editForm.name" size="30" @keyup.enter="saveSection(s.code)" />
              </template>
              <template v-else>{{ s.name }}</template>
            </td>
            <td>
              <input type="checkbox" :checked="s.is_active"
                @change="toggleSection(s)" :disabled="saving === s.code" />
            </td>
            <td>
              <input type="number" :value="s.sorting_order" size="3" style="width:60px"
                @change="reorderSection(s, $event)" :disabled="saving === s.code" />
            </td>
            <td>
              <button v-if="editingSection !== s.code" class="btn-sm" @click="startEdit(s)">✎</button>
              <button v-else class="btn-sm btn-save" @click="saveSection(s.code)">✓</button>
              <button v-if="editingSection === s.code" class="btn-sm" @click="editingSection = null">✕</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="loading">Загрузка...</div>
    </section>

    <!-- === TAB 2: Permission Matrix === -->
    <section v-if="tab === 'matrix'" class="tab-panel">
      <!-- Выбор организации -->
      <div class="sel-row">
        <label>Организация:</label>
        <select v-model="selectedCust" @change="loadMatrix" :disabled="loading">
          <option :value="null">— выберите —</option>
          <option v-for="c in customers" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <span v-if="loading" class="spinner">⏳</span>
        <span v-if="matrixSaveMsg" :class="matrixSaveErr ? 'err' : 'ok'">{{ matrixSaveMsg }}</span>
      </div>

      <template v-if="matrix">
        <h3>Организация: {{ matrix.customer_name }}</h3>

        <!-- Потолок прав -->
        <fieldset>
          <legend>Видимые разделы (потолок организации)</legend>
          <label v-for="s in matrix.all_sections" :key="'org-'+s.code" class="chk-inline">
            <input type="checkbox" :value="s.code" v-model="editOrgSections" :disabled="!s.is_active" />
            {{ s.name || s.code }}
          </label>
        </fieldset>

        <!-- Роли -->
        <fieldset>
          <legend>Роли</legend>
          <div v-if="editRoles.length" class="perm-block">
            <PermissionMatrix
              :sections="matrix.all_sections"
              :rows="editRoles"
              rowLabelKey="name"
              checkedKey="section_permissions"
              :orgSections="editOrgSections"
              @toggle="onRoleToggle"
            />
          </div>
          <div v-else class="empty">Нет ролей</div>
        </fieldset>

        <!-- Пользователи -->
        <fieldset>
          <legend>Пользователи</legend>
          <div v-if="editUsers.length" class="perm-block">
            <PermissionMatrix
              :sections="matrix.all_sections"
              :rows="editUsers"
              rowLabelKey="name"
              checkedKey="individual_sections"
              inheritedKey="role_sections"
              :orgSections="editOrgSections"
              @toggle="onUserToggle"
            />
          </div>
          <div v-else class="empty">Нет пользователей</div>
        </fieldset>

        <div class="actions">
          <button class="btn-primary" @click="saveMatrix" :disabled="savingMatrix">
            {{ savingMatrix ? 'Сохранение...' : 'Сохранить изменения' }}
          </button>
        </div>
      </template>
      <div v-else-if="selectedCust" class="loading">Загрузка матрицы...</div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/shared/api'
import PermissionMatrix from '@/shared/components/PermissionMatrix.vue'

const tab = ref('sections')

// —— TAB 1: SiteSections ——
const siteSections = ref([])
const editingSection = ref(null)
const saving = ref(null)
const editForm = reactive({ name: '' })

async function loadSections() {
  try {
    const r = await api.get('/admin/site-sections/')
    siteSections.value = r.data.sections || []
  } catch (e) { /* handled by interceptor */ }
}

function startEdit(s) {
  editingSection.value = s.code
  editForm.name = s.name
}

async function toggleSection(s) {
  const newVal = !s.is_active
  saving.value = s.code
  try {
    await api.put(`/admin/site-sections/${s.code}/`, { is_active: newVal })
    s.is_active = newVal
  } catch (e) { /* */ }
  finally { saving.value = null }
}

function reorderSection(s, ev) {
  const val = parseInt(ev.target.value, 10)
  if (isNaN(val)) return
  const prev = s.sorting_order
  s.sorting_order = val
  api.put(`/admin/site-sections/${s.code}/`, { sorting_order: val }).catch(() => {
    s.sorting_order = prev  // rollback on error
  })
}

async function saveSection(code) {
  saving.value = code
  try {
    await api.put(`/admin/site-sections/${code}/`, { name: editForm.name })
    const s = siteSections.value.find(x => x.code === code)
    if (s) s.name = editForm.name
    editingSection.value = null
  } catch (e) { /* */ }
  finally { saving.value = null }
}

// —— TAB 2: Permission Matrix ——
const customers = ref([])
const selectedCust = ref(null)
const matrix = ref(null)
const loading = ref(false)
const savingMatrix = ref(false)
const matrixSaveMsg = ref('')
const matrixSaveErr = ref(false)

// Editable copies
const editOrgSections = ref([])
const editRoles = ref([])
const editUsers = ref([])

async function loadCustomers() {
  try {
    const r = await api.get('/admin/customers/')
    customers.value = r.data.customers || []
  } catch (e) { /* */ }
}

async function loadMatrix() {
  if (!selectedCust.value) { matrix.value = null; return }
  loading.value = true
  try {
    const r = await api.get(`/admin/customers/${selectedCust.value}/permission-matrix/`)
    matrix.value = r.data
    // Create editable deep copies
    editOrgSections.value = [...(r.data.org_sections || [])]
    editRoles.value = (r.data.roles || []).map(r => ({
      ...r,
      section_permissions: [...(r.section_permissions || [])],
    }))
    editUsers.value = (r.data.users || []).map(u => ({
      ...u,
      individual_sections: [...(u.individual_sections || [])],
      role_sections: [...(u.role_sections || [])],
      effective_sections: [...(u.effective_sections || [])],
    }))
    matrixSaveMsg.value = ''
  } catch (e) { /* */ }
  finally { loading.value = false }
}

function onRoleToggle(row, code) {
  const idx = row.section_permissions.indexOf(code)
  if (idx >= 0) row.section_permissions.splice(idx, 1)
  else row.section_permissions.push(code)
  matrixSaveMsg.value = ''
}

function onUserToggle(row, code) {
  const idx = row.individual_sections.indexOf(code)
  if (idx >= 0) {
    row.individual_sections.splice(idx, 1)
  } else {
    // Добавляем явное индивидуальное разрешение (поверх ролевого)
    row.individual_sections.push(code)
  }
  matrixSaveMsg.value = ''
}

async function saveMatrix() {
  savingMatrix.value = true
  matrixSaveMsg.value = ''
  matrixSaveErr.value = false
  const cid = selectedCust.value
  try {
    // 1. Save org-level: visible_sections + roles
    await api.post(`/admin/customers/${cid}/`, {
      visible_sections: editOrgSections.value,
      roles: editRoles.value.map(r => ({
        id: r.id,
        code: r.code,
        name: r.name,
        is_default: r.is_default,
        section_permissions: r.section_permissions,
      })),
    })

    // 2. Save each user's individual section_permissions
    for (const u of editUsers.value) {
      await api.put(`/admin/customers/${cid}/users/`, {
        id: u.id,
        section_permissions: u.individual_sections,
      })
    }

    matrixSaveMsg.value = 'Сохранено'
    await loadMatrix() // Refresh to show effective permissions
  } catch (e) {
    // Частичное сохранение: перезагружаем матрицу чтобы показать реальное состояние БД
    await loadMatrix().catch(() => {})
    matrixSaveMsg.value = 'Ошибка: ' + (e.response?.data?.error || e.message)
    matrixSaveErr.value = true
  }
  finally { savingMatrix.value = false }
}

onMounted(() => {
  loadSections()
  loadCustomers()
})
</script>

<style scoped>
.perm-page { max-width: 1400px; margin: 0 auto; padding: 20px; }
h2 { margin-bottom: 16px; }
h3 { font-size: 16px; margin: 16px 0 8px; }

/* Tabs */
.tabs { display: flex; gap: 0; margin-bottom: 20px; border-bottom: 2px solid var(--cat-border, #c8c4bc); }
.tabs button {
  padding: 8px 24px; font-size: 14px; font-weight: 500;
  border: none; background: transparent; color: var(--cat-muted, #7a7a7a);
  cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -2px;
}
.tabs button.active {
  color: var(--cat-primary, #5785b5);
  border-bottom-color: var(--cat-primary, #5785b5);
}
.tabs button:hover:not(.active) { color: var(--cat-text, #1c1c1c); }

/* Tab panels */
.tab-panel { min-height: 200px; }

/* Data table */
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th, .data-table td { padding: 8px 10px; border-bottom: 1px solid var(--cat-border-light, #e0dcd6); text-align: left; }
.data-table th { background: var(--cat-bg, #f5f2ed); font-weight: 600; }
.inactive { opacity: 0.5; }
code { background: var(--cat-bg, #f5f2ed); padding: 2px 6px; border-radius: 3px; font-size: 12px; }

/* Buttons */
.btn-sm { padding: 2px 8px; font-size: 12px; border: 1px solid var(--cat-border, #c8c4bc); border-radius: 3px; background: var(--cat-surface, #fff); cursor: pointer; }
.btn-sm:hover { border-color: var(--cat-primary, #5785b5); }
.btn-save { color: #2e7d32; border-color: #2e7d32; }
.btn-primary {
  padding: 10px 32px; font-size: 14px; font-weight: 500;
  background: var(--cat-primary, #5785b5); color: #fff;
  border: none; border-radius: var(--cat-radius-md, 3px); cursor: pointer;
}
.btn-primary:disabled { opacity: 0.5; cursor: default; }

/* Select + row */
.sel-row { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
.sel-row select { padding: 6px 10px; border: 1px solid var(--cat-border, #c8c4bc); border-radius: 3px; font-size: 14px; }
.chk-inline { display: inline-block; margin-right: 12px; font-size: 13px; }

/* Fieldsets */
fieldset { border: 1px solid var(--cat-border-light, #e0dcd6); border-radius: 4px; padding: 12px 16px; margin-bottom: 16px; }
legend { font-weight: 600; font-size: 14px; padding: 0 8px; }

.perm-block { margin-top: 8px; }
.actions { margin-top: 20px; }
.empty { padding: 20px; color: var(--cat-muted-light, #a0a0a0); text-align: center; }
.loading { padding: 40px; text-align: center; color: var(--cat-muted, #7a7a7a); }
.spinner { color: var(--cat-muted, #7a7a7a); }
.err { color: #c0504d; font-size: 13px; }
.ok { color: #2e7d32; font-size: 13px; }
</style>
