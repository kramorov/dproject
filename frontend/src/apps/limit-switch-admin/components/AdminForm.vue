<!-- apps/limit-switch-admin/components/AdminForm.vue — обёртка модалки CRUD с защитой от потери изменений -->
<template>
  <BaseModal :show="show" :title="title" width="900px" :closable="false" @close="handleClose">
    <div class="af-body" v-if="show">
      <slot :form="form" :opts="opts" />

      <div v-if="error" class="af-error">{{ error }}</div>

      <div class="af-actions">
        <button class="af-save" :disabled="saving" @click="doSave">
          {{ saving ? 'Сохранение...' : (isNew ? 'Создать' : 'Сохранить') }}
        </button>
        <button v-if="!isNew" class="af-copy" :disabled="copying" @click="doCopy">
          {{ copying ? 'Копирование...' : 'Копировать' }}
        </button>
        <button v-if="!isNew" class="af-del" :disabled="deleting" @click="doDelete">
          {{ deleting ? 'Удаление...' : 'Удалить' }}
        </button>
        <button class="af-close" @click="handleClose">Закрыть</button>
      </div>
    </div>
  </BaseModal>

  <!-- Модалка несохранённых изменений -->
  <div v-if="showUnsaved" class="af-overlay" @click.self="showUnsaved = false">
    <div class="af-confirm">
      <p>Имеются несохранённые данные.</p>
      <p>Закрыть без сохранения?</p>
      <div class="af-confirm-btns">
        <button class="af-btn-yes" @click="forceClose">Да, закрыть</button>
        <button class="af-btn-no" @click="showUnsaved = false">Нет, продолжить редактирование</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import BaseModal from '@/shared/components/BaseModal.vue'

const props = defineProps({
  show: Boolean,
  title: { type: String, default: '' },
  item: { type: Object, default: null },
  api: { type: Object, required: true },
  formRef: { type: Object, default: null },
  opts: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['saved', 'deleted', 'cancel', 'copied'])

const saving = ref(false)
const deleting = ref(false)
const copying = ref(false)
const error = ref(null)
const form = ref({})
const showUnsaved = ref(false)
const initialData = ref(null)

const isNew = computed(() => !props.item?.id)

// Снимаем снапшот начальных данных при открытии
watch(() => props.show, async (v) => {
  if (v) {
    initialData.value = null
    showUnsaved.value = false
    // Ждём рендера дочерней формы
    await nextTick()
    setTimeout(() => {
      if (props.formRef?.getFormData) {
        initialData.value = JSON.stringify(props.formRef.getFormData())
      }
    }, 300)
  }
})

function getFormData() {
  return props.formRef?.getFormData?.() || {}
}

function hasChanges() {
  if (!initialData.value || !props.formRef?.getFormData) return false
  const current = JSON.stringify(props.formRef.getFormData())
  return current !== initialData.value
}

function handleClose() {
  if (!isNew.value && hasChanges()) {
    showUnsaved.value = true
    return
  }
  forceClose()
}

function forceClose() {
  showUnsaved.value = false
  initialData.value = null
  emit('cancel')
}

async function doSave() {
  saving.value = true; error.value = null
  try {
    const data = getFormData()
    if (isNew.value) {
      await props.api.create(data)
    } else {
      await props.api.update(props.item.id, data)
    }
    // Обновляем снапшот после сохранения
    initialData.value = JSON.stringify(data)
    emit('saved')
  } catch (e) {
    error.value = e.displayMessage || e.response?.data?.error || e.message || 'Ошибка сохранения'
  } finally { saving.value = false }
}

async function doDelete() {
  if (!confirm('Удалить запись? Это действие необратимо.')) return
  deleting.value = true; error.value = null
  try {
    await props.api.remove(props.item.id)
    emit('deleted')
  } catch (e) {
    error.value = e.displayMessage || e.message || 'Ошибка удаления'
  } finally { deleting.value = false }
}

async function doCopy() {
  copying.value = true; error.value = null
  try {
    const data = getFormData()
    data.name = (data.name || '') + ' (Копия)'
    if (data.code) data.code = data.code + '_copy'
    const res = await props.api.create(data)
    emit('copied', res.data)
  } catch (e) {
    error.value = e.displayMessage || e.message || 'Ошибка копирования'
  } finally { copying.value = false }
}

defineExpose({ form })
</script>

<style scoped>
.af-body { display: flex; flex-direction: column; gap: 12px; max-height: 70vh; overflow-y: auto; padding: 4px 0; }
.af-error { color: #dc2626; font-size: 13px; padding: 6px 10px; background: #fef2f2; border-radius: 4px; }
.af-actions { display: flex; gap: 8px; justify-content: flex-end; padding-top: 8px; border-top: 1px solid #e5e7eb; }
.af-actions button { padding: 6px 16px; border-radius: 5px; cursor: pointer; font-size: 13px; border: 1px solid #d1d5db; }
.af-save { background: #2563eb; color: #fff; border-color: #2563eb; }
.af-save:hover:not(:disabled) { background: #1d4ed8; }
.af-copy { background: #fff; }
.af-copy:hover:not(:disabled) { background: #f0f9ff; }
.af-del { background: #fff; color: #dc2626; border-color: #dc2626; }
.af-del:hover:not(:disabled) { background: #fef2f2; }
.af-close { background: #fff; }
.af-close:hover { background: #f3f4f6; }
.af-actions button:disabled { opacity: .5; cursor: default; }

/* Confirmation overlay */
.af-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.4); display: flex; align-items: center; justify-content: center; z-index: 1200; }
.af-confirm { background: #fff; border-radius: 10px; padding: 24px 28px; max-width: 420px; box-shadow: 0 8px 32px rgba(0,0,0,.15); }
.af-confirm p { margin: 0 0 8px; font-size: 14px; color: #1f2937; }
.af-confirm p:last-of-type { margin-bottom: 16px; }
.af-confirm-btns { display: flex; gap: 8px; justify-content: flex-end; }
.af-btn-yes { padding: 6px 16px; border: 1px solid #dc2626; border-radius: 6px; background: #fff; color: #dc2626; cursor: pointer; font-size: 13px; }
.af-btn-yes:hover { background: #fef2f2; }
.af-btn-no { padding: 6px 16px; border: 1px solid #2563eb; border-radius: 6px; background: #2563eb; color: #fff; cursor: pointer; font-size: 13px; }
.af-btn-no:hover { background: #1d4ed8; }
</style>
