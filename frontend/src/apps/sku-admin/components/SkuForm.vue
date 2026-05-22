<template>
  <div class="modal-bg" @click.self="$emit('close')">
    <div class="modal">
      <h3>{{ isNew ? 'Создать SKU' : 'Редактировать SKU' }}</h3>
      <div class="body">
        <label>Код <span class="req">*</span></label>
        <input v-model="form.code" class="inp" :disabled="!isNew" />
        <label>Название</label>
        <input v-model="form.name" class="inp" />
        <label>Описание</label>
        <textarea v-model="form.description" class="inp" rows="3"></textarea>
        <label>Тип оборудования</label>
        <select v-model="form.equipment_type_id" class="inp"><option :value="null">—</option>
          <option v-for="t in opts.equipmentTypes" :key="t.id" :value="t.id">{{ t.name }}</option></select>
        <label>Бренд</label>
        <select v-model="form.brand_id" class="inp"><option :value="null">—</option>
          <option v-for="b in opts.brands" :key="b.id" :value="b.id">{{ b.name }}</option></select>
        <label><input type="checkbox" v-model="form.is_active" /> Активно</label>
      </div>
      <div class="btns">
        <button v-if="!isNew" @click="doDelete" class="btn-del">Удалить</button>
        <button @click="$emit('close')" class="btn-cancel">Отмена</button>
        <button @click="doSave" class="btn-save" :disabled="saving">{{ saving ? '...' : 'Сохранить' }}</button>
      </div>
      <div v-if="error" class="err">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, inject, computed, watch } from 'vue'
import skuApi from '../api'

const props = defineProps({ sku: Object })
const emit = defineEmits(['close', 'saved'])
const opts = inject('opts')

const isNew = computed(() => !props.sku?.id)

const form = reactive({
  code: '', name: '', description: '',
  equipment_type_id: null, brand_id: null, is_active: true,
})

const saving = ref(false), error = ref('')

watch(() => props.sku, (s) => {
  if (s) {
    form.code = s.code || ''
    form.name = s.name || ''
    form.description = s.description || ''
    form.equipment_type_id = s.equipment_type_id || null
    form.brand_id = s.brand_id || null
    form.is_active = s.is_active !== false
  } else {
    Object.assign(form, { code:'', name:'', description:'', equipment_type_id:null, brand_id:null, is_active:true })
  }
}, { immediate: true })

async function doSave() {
  if (!form.code.trim()) { error.value = 'Код обязателен'; return }
  saving.value = true; error.value = ''
  try {
    const data = {
      code: form.code.trim(),
      name: form.name.trim(),
      description: form.description.trim(),
      equipment_type_id: form.equipment_type_id || null,
      brand_id: form.brand_id || null,
      is_active: form.is_active,
    }
    if (isNew.value) {
      await skuApi.create(data)
    } else {
      await skuApi.update(props.sku.id, data)
    }
    emit('saved')
  } catch (e) {
    error.value = e.displayMessage || e.message || 'Ошибка сохранения'
  } finally { saving.value = false }
}

async function doDelete() {
  if (!confirm('Удалить SKU? Связанные цены также будут удалены.')) return
  try {
    await skuApi.delete(props.sku.id)
    emit('saved')
  } catch (e) {
    error.value = e.displayMessage || e.message || 'Ошибка удаления'
  }
}
</script>

<style scoped>
.modal-bg{position:fixed;inset:0;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;z-index:100}
.modal{background:#fff;border-radius:8px;padding:24px;width:520px;max-height:90vh;overflow-y:auto;box-shadow:0 4px 24px rgba(0,0,0,.15)}
h3{margin:0 0 16px;font-size:18px}
.body{display:flex;flex-direction:column;gap:6px}
label{font-size:13px;color:#374151;display:flex;align-items:center;gap:4px}
.req{color:#dc2626}
.inp{padding:6px 10px;border:1px solid #d1d5db;border-radius:5px;font-size:13px}
.btns{display:flex;gap:8px;margin-top:16px;justify-content:flex-end}
.btns button{padding:6px 16px;border-radius:5px;cursor:pointer;font-size:13px;border:1px solid #d1d5db}
.btn-save{background:#2563eb;color:#fff;border-color:#2563eb}
.btn-save:hover{background:#1d4ed8}
.btn-cancel{background:#fff}
.btn-del{background:#fff;color:#dc2626;border-color:#dc2626;margin-right:auto}
.btn-del:hover{background:#fef2f2}
.err{color:#dc2626;font-size:13px;margin-top:8px}
</style>
