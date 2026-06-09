<template>
  <div class="doc-card" v-if="doc">
    <!-- Ошибка -->
    <div v-if="error" class="card-error">{{ error }}</div>

    <!-- Заголовок -->
    <div class="card-header">
      <div class="header-left">
        <h2 class="doc-title">{{ doc.name || 'Без названия' }}</h2>
        <span class="doc-code" v-if="doc.code">{{ doc.code }}</span>
        <span :class="statusBadgeClass">{{ statusLabel }}</span>
      </div>
      <div class="header-right">
        <BaseButton v-if="canSave" variant="primary" :loading="saving" @click="$emit('save')">
          Сохранить
        </BaseButton>
      </div>
    </div>

    <!-- Реквизиты -->
    <div class="card-body">
      <div class="card-section">
        <h3>Реквизиты</h3>
        <div class="form-grid">
          <label>
            <span>Название</span>
            <input v-model="form.name" :disabled="!isDraft" class="form-input" />
          </label>
          <label>
            <span>Дата</span>
            <input type="date" v-model="form.document_date" :disabled="!isDraft" class="form-input" />
          </label>
          <label class="span-2">
            <span>Комментарий</span>
            <textarea v-model="form.description" :disabled="!isDraft" class="form-input" rows="2"></textarea>
          </label>
        </div>
      </div>

      <!-- Строки (слот) -->
      <div class="card-section">
        <h3>Позиции</h3>
        <slot name="items" :doc="doc" :is-draft="isDraft">
          <p class="text-muted">Нет позиций</p>
        </slot>
      </div>

      <!-- Действия -->
      <div class="card-actions">
        <div class="actions-left">
          <!-- Статусные -->
          <AppButton v-if="canRegister" variant="primary" :disabled="saving" @click="onAction('register')">✓ Провести</AppButton>
          <AppButton v-if="canUnregister" variant="cancel" :disabled="saving" @click="onAction('unregister')">↩ Отменить проведение</AppButton>
          <AppButton v-if="canMarkDeleted" variant="danger" :disabled="saving" @click="onAction('mark-deleted')">✕ Пометить на удаление</AppButton>
          <AppButton v-if="canRestore" variant="ghost" :disabled="saving" @click="onAction('restore')">↩ Отменить удаление</AppButton>
        </div>
        <div class="actions-right">
          <!-- Печать / Экспорт / Импорт — только если features разрешают -->
          <AppButton v-if="features.print" variant="ghost" @click="onAction('print')">🖨 Печать</AppButton>

          <div v-if="availableExports.length" class="export-group">
            <AppButton variant="ghost" @click="showExport = !showExport">📥 Экспорт ▾</AppButton>
            <div v-if="showExport" class="export-dropdown">
              <button
                v-for="exp in availableExports"
                :key="exp.key"
                @click="onAction('export', exp.key)"
                class="dropdown-item"
              >{{ exp.label }}</button>
            </div>
          </div>

          <label v-if="features.import && isDraft" class="import-label">
            <AppButton variant="ghost" as="span">📤 Импорт</AppButton>
            <input type="file" hidden @change="onImportFile" accept=".xlsx,.xls,.csv" />
          </label>
        </div>
      </div>
    </div>

    <!-- Загрузка -->
    <Spinner v-if="loading" text="Загрузка..." />

    <!-- Подтверждение -->
    <BaseModal :show="!!confirmAction" title="Подтверждение" width="360px" @close="confirmAction = null">
      <p style="text-align:center; margin:0 0 16px;">{{ confirmAction?.message }}</p>
      <div class="confirm-buttons">
        <AppButton variant="primary" @click="doConfirm">Да</AppButton>
        <AppButton variant="cancel" @click="confirmAction = null">Отмена</AppButton>
      </div>
    </BaseModal>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import AppButton from '@/shared/components/AppButton.vue'
import BaseButton from '@/shared/components/BaseButton.vue'
import BaseModal from '@/shared/components/BaseModal.vue'
import Spinner from '@/shared/components/Spinner.vue'

const props = defineProps({
  doc: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  saving: { type: Boolean, default: false },
  error: { type: String, default: '' },
  form: { type: Object, required: true },
  isDraft: { type: Boolean, default: false },
  isPosted: { type: Boolean, default: false },
  isDeleted: { type: Boolean, default: false },
  features: { type: Object, default: () => ({}) },
  canSave: { type: Boolean, default: false },
  canRegister: { type: Boolean, default: false },
  canUnregister: { type: Boolean, default: false },
  canMarkDeleted: { type: Boolean, default: false },
  canRestore: { type: Boolean, default: false },
  availableExports: { type: Array, default: () => [] },
})

const emit = defineEmits([
  'save', 'register', 'unregister', 'mark-deleted', 'restore',
  'print', 'export', 'import-file',
])

const showExport = ref(false)
const confirmAction = ref(null)

const statusLabel = computed(() => {
  if (!props.doc) return ''
  return props.doc.status_label || props.doc.status || ''
})

const statusBadgeClass = computed(() => {
  const s = props.doc?.status || 'draft'
  return 'status-badge status-' + s
})

function onAction(action, payload) {
  const messages = {
    'register': 'Провести документ?',
    'unregister': 'Отменить проведение?',
    'mark-deleted': 'Пометить документ на удаление?',
  }
  if (messages[action]) {
    confirmAction.value = { action, payload, message: messages[action] }
  } else {
    emit(action, payload)
  }
}

function doConfirm() {
  if (!confirmAction.value) return
  const { action, payload } = confirmAction.value
  confirmAction.value = null
  emit(action, payload)
}

function onImportFile(e) {
  const file = e.target.files?.[0]
  if (file) emit('import-file', file)
  e.target.value = ''
}
</script>

<style scoped>
.doc-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--cat-gap-lg);
  font-family: var(--cat-font);
  font-size: var(--cat-text-sm);
}
.card-error {
  background: var(--cat-badge-deleted-bg);
  color: var(--cat-status-deleted);
  padding: var(--cat-gap-sm) var(--cat-gap-md);
  border-radius: var(--cat-radius-sm);
  font-size: var(--cat-text-xs);
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: var(--cat-gap-md);
}
.header-left { display: flex; align-items: baseline; gap: var(--cat-gap-sm); flex-wrap: wrap; }
.doc-title { font-size: var(--cat-header-title-size); font-weight: var(--cat-header-title-weight); margin: 0; }
.doc-code { font-family: var(--cat-font-mono); font-size: var(--cat-header-code-size); color: var(--cat-muted); background: var(--cat-border-light); padding: 1px 6px; border-radius: var(--cat-radius-sm); }

.status-badge { font-size: var(--cat-text-xs); padding: 1px 8px; border-radius: var(--cat-radius-sm); font-weight: 600; }
.status-draft { background: var(--cat-badge-draft-bg); color: var(--cat-status-draft); }
.status-on_approval { background: var(--cat-badge-approval-bg); color: var(--cat-status-approval); }
.status-posted { background: var(--cat-badge-posted-bg); color: var(--cat-status-posted); }
.status-deleted { background: var(--cat-badge-deleted-bg); color: var(--cat-status-deleted); }

.card-body { display: flex; flex-direction: column; gap: var(--cat-gap-xl); }
.card-section h3 { font-size: var(--cat-text-base); font-weight: 700; margin: 0 0 var(--cat-gap-sm); color: var(--cat-text); border-bottom: 1px solid var(--cat-header-border); padding-bottom: 3px; }

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--cat-gap-sm);
}
.form-grid label { display: flex; flex-direction: column; gap: var(--cat-gap-xs); font-size: var(--cat-text-xs); color: var(--cat-muted); }
.form-grid .span-2 { grid-column: span 2; }
.form-input {
  padding: 2px 6px;
  border: 1px solid var(--cat-input-border, var(--cat-border));
  border-radius: var(--cat-radius-sm);
  font-size: var(--cat-text-sm);
  font-family: var(--cat-font);
  background: var(--cat-input-bg, #fff);
}
.form-input:focus-visible { border-color: var(--cat-input-focus-border, var(--cat-primary)); box-shadow: 0 0 0 1px var(--cat-input-focus-border, var(--cat-primary)); outline: none; }
.form-input:disabled { background: var(--cat-input-disabled-bg); color: var(--cat-muted); }

.text-muted { color: var(--cat-muted); font-size: var(--cat-text-sm); }

.card-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--cat-gap-sm);
  padding-top: var(--cat-gap-md);
  border-top: 1px solid var(--cat-header-border);
}
.actions-left, .actions-right { display: flex; gap: var(--cat-gap-sm); align-items: center; flex-wrap: wrap; }
.export-group { position: relative; }
.export-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: var(--cat-gap-xs);
  background: var(--cat-surface);
  border: 1px solid var(--cat-border);
  border-radius: var(--cat-radius-sm);
  box-shadow: var(--cat-shadow-card);
  z-index: 10;
  min-width: 120px;
}
.dropdown-item {
  display: block;
  width: 100%;
  padding: 3px 10px;
  border: none;
  background: none;
  text-align: left;
  cursor: pointer;
  font-size: var(--cat-text-sm);
  font-family: var(--cat-font);
}
.dropdown-item:hover { background: var(--cat-primary-light); }
.import-label { cursor: pointer; display: inline-flex; }

.confirm-buttons { display: flex; gap: var(--cat-gap-sm); justify-content: center; }
</style>