<!-- shared/components/catalog/PaActuatorConfigurator.vue -->
<!-- Специализированный конфигуратор пневмоприводов.
     В отличие от каталогов других типов оборудования у ПП нет готового артикула
     (model_line_item — это только «корпус + DA/SR»); полная конфигурация собирается
     из серии + выбранных опций. Поэтому здесь НЕ используется общий паттерн
     «просмотр серия → артикулы», а только каскад: серия → типоразмер → опции. -->
<template>
  <div class="pa-config">
    <PageTitle
      :title="title"
      :subtitle="subtitle"
    />

    <div v-if="loadingML" class="state"><Spinner /></div>
    <div v-else-if="!modelLines.length" class="empty">Нет доступных серий</div>

    <template v-else>
      <!-- 1. Серия -->
      <div class="step">
        <div class="step-label">Серия</div>
        <div class="chips">
          <button
            v-for="ml in modelLines"
            :key="ml.id"
            class="chip"
            :class="{ active: form.model_line_id === ml.id }"
            @click="selectML(ml.id)"
          >{{ ml.name }}</button>
        </div>
      </div>

      <!-- 2. Тип привода + типоразмер -->
      <div class="step" v-if="form.model_line_id">
        <div class="step-label">Тип привода</div>
        <div class="chips">
          <button
            class="chip"
            :class="{ active: form.variety === 'DA' }"
            @click="selectVariety('DA')"
          >DA — двойного действия</button>
          <button
            class="chip"
            :class="{ active: form.variety === 'SR' }"
            @click="selectVariety('SR')"
          >SR — с возвратной пружиной</button>
        </div>

        <div class="step-label" v-if="form.variety">Модель</div>
        <div class="chips" v-if="form.variety">
          <button
            v-for="item in modelItems"
            :key="item.id"
            class="chip"
            :class="{ active: form.model_line_item_id === item.id }"
            @click="selectItem(item.id)"
          >{{ item.name }}</button>
        </div>
      </div>

      <!-- 3. Опции -->
      <div class="step" v-if="optionFields.length">
        <div class="step-label">Опции</div>
        <div class="options">
          <div class="option" v-for="opt in optionFields" :key="opt.key">
            <label>{{ opt.label }}</label>
            <select :value="form[opt.key]" @change="toggleOption(opt.key, $event.target.value)">
              <option :value="null">— не выбрано —</option>
              <option
                v-for="o in opt.items"
                :key="o.id"
                :value="o.id"
              >{{ o.name }}{{ o.is_default ? ' (стандарт)' : '' }}</option>
            </select>
          </div>
        </div>
      </div>

      <!-- 4. Результат -->
      <div class="result" v-if="preview">
        <PaProductCard
          :preview="preview"
          @add-to-cart="$emit('addToCart', buildPayload())"
        />
      </div>
      <div v-else-if="loading" class="state"><Spinner /></div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import PageTitle from '@/shared/components/PageTitle.vue'
import Spinner from '@/shared/components/Spinner.vue'
import PaProductCard from './PaProductCard.vue'

const props = defineProps({
  api: { type: Object, required: true },
  title: { type: String, default: 'Конфигуратор пневмопривода' },
  subtitle: { type: String, default: 'Серия → типоразмер → опции' },
  // Предвыбор серии (из CatalogSection, единый паттерн)
  initialModelLineId: { type: Number, default: null },
})
defineEmits(['addToCart'])

const OPTION_KEY_MAP = {
  safety_positions: 'safety_position',
  springs_qty_options: 'springs_qty',
  temperature_options: 'temperature',
  ip_options: 'ip',
  exd_options: 'exd',
  body_coating_options: 'body_coating',
  hand_wheel_options: 'hand_wheel',
}

const OPTION_LABELS = {
  safety_position: 'Положение безопасности',
  springs_qty: 'Количество пружин',
  temperature: 'Температурное исполнение',
  ip: 'Степень защиты IP',
  exd: 'Взрывозащита',
  body_coating: 'Покрытие корпуса',
  hand_wheel: 'Ручной дублёр',
}

const OPTION_KEYS = ['springs_qty', 'temperature', 'safety_position', 'ip', 'exd', 'body_coating', 'hand_wheel']

const modelLines = ref([])
const modelItems = ref([])
const optionFields = ref([])
const preview = ref(null)
const loadingML = ref(false)
const loading = ref(false)

const form = reactive({
  model_line_id: null,
  variety: null,
  model_line_item_id: null,
  springs_qty: null, temperature: null, safety_position: null,
  ip: null, exd: null, body_coating: null, hand_wheel: null,
})

onMounted(async () => {
  loadingML.value = true
  try {
    const { data } = await props.api.getModelLines()
    modelLines.value = data || []
  } catch (e) {
    console.error('PaActuatorConfigurator: model_lines failed', e)
  }
  loadingML.value = false

  if (props.initialModelLineId) {
    await selectML(props.initialModelLineId)
  }
})

async function selectML(id) {
  if (form.model_line_id === id) return
  form.model_line_id = id
  form.variety = null
  resetAfter('model_line_id')
  await autoSelectVariety()
}

async function autoSelectVariety() {
  // Первый тип привода (DA/SR), у которого есть model_line_item, и первый item.
  for (const v of ['DA', 'SR']) {
    try {
      const { data } = await props.api.getModelLineItems(form.model_line_id, v)
      if (data && data.length) {
        form.variety = v
        modelItems.value = data
        await selectItem(data[0].id)
        return
      }
    } catch (e) {
      console.error('PaActuatorConfigurator: autoSelect items failed', e)
    }
  }
  form.variety = null
  modelItems.value = []
}

async function selectVariety(v) {
  if (form.variety === v) return
  form.variety = v
  resetAfter('variety')
  loading.value = true
  try {
    const { data } = await props.api.getModelLineItems(form.model_line_id, v)
    modelItems.value = data || []
  } catch (e) {
    console.error('PaActuatorConfigurator: items failed', e)
    modelItems.value = []
  }
  loading.value = false
  if (modelItems.value.length) {
    await selectItem(modelItems.value[0].id)
  }
}

async function selectItem(id) {
  if (form.model_line_item_id === id) return
  form.model_line_item_id = id
  for (const k of OPTION_KEYS) form[k] = null
  optionFields.value = []
  preview.value = null

  loading.value = true
  try {
    const { data } = await props.api.getOptions(id)
    const fields = []
    for (const [apiKey, items] of Object.entries(data || {})) {
      if (!Array.isArray(items) || !items.length) continue
      const formKey = OPTION_KEY_MAP[apiKey]
      if (!formKey) continue
      const mapped = items.map(o => ({
        id: o.option_id || o.id,
        name: o.name,
        is_default: o.is_default,
      }))
      fields.push({ key: formKey, label: OPTION_LABELS[formKey] || formKey, items: mapped })
      const def = mapped.find(o => o.is_default) || mapped[0]
      if (def && form[formKey] === null) form[formKey] = def.id
    }
    optionFields.value = fields
    await fetchPreview()
  } catch (e) {
    console.error('PaActuatorConfigurator: options failed', e)
  }
  loading.value = false
}

function toggleOption(key, value) {
  const v = value === '' || value === null ? null : Number(value)
  if (form[key] === v) return
  form[key] = v
  fetchPreview()
}

async function fetchPreview() {
  if (!form.model_line_item_id) return
  try {
    const { data } = await props.api.preview({
      selected_model_line_item: form.model_line_item_id,
      selected_safety_position: form.safety_position,
      selected_springs_qty: form.springs_qty,
      selected_temperature: form.temperature,
      selected_ip: form.ip,
      selected_exd: form.exd,
      selected_body_coating: form.body_coating,
      selected_hand_wheel: form.hand_wheel,
    })
    preview.value = data
  } catch (e) {
    console.error('PaActuatorConfigurator: preview failed', e)
  }
}

function resetAfter(field) {
  const order = ['model_line_id', 'variety', 'model_line_item_id']
  const idx = order.indexOf(field)
  for (let i = idx + 1; i < order.length; i++) form[order[i]] = null
  modelItems.value = []
  optionFields.value = []
  preview.value = null
}

function buildPayload() {
  const opts = {}
  for (const k of OPTION_KEYS) if (form[k] != null) opts[k] = form[k]
  return { model_line_item_id: form.model_line_item_id, options: opts }
}
</script>

<style scoped>
.pa-config { max-width: 1200px; margin: 0 auto; padding: var(--cat-gap-lg, 16px); }
.step { margin-bottom: var(--cat-gap-xl, 20px); }
.step-label {
  font-weight: 600; font-size: var(--cat-text-sm, 13px); color: var(--cat-text-soft, #374151);
  margin: 10px 0 6px;
}
.chips { display: flex; flex-wrap: wrap; gap: var(--cat-gap-xs, 6px); }
.chip {
  padding: 6px 14px; font-size: var(--cat-text-sm, 13px);
  border: 1px solid var(--cat-border, #e5e7eb); border-radius: 18px;
  background: var(--cat-surface, #fff); color: var(--cat-text, #1f2937); cursor: pointer;
  transition: all .12s; white-space: nowrap;
}
.chip:hover { border-color: var(--cat-primary, #2563eb); color: var(--cat-primary, #2563eb); }
.chip.active { background: var(--cat-primary, #2563eb); color: #fff; border-color: var(--cat-primary, #2563eb); }

.options { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: var(--cat-gap-md, 12px); }
.option label { display: block; font-size: var(--cat-text-xs, 12px); color: var(--cat-muted, #6b7280); margin-bottom: 4px; }
.option select {
  width: 100%; padding: 8px; font-size: var(--cat-text-sm, 13px);
  border: 1px solid var(--cat-border, #e5e7eb); border-radius: var(--cat-radius-md, 8px); background: var(--cat-surface, #fff); color: var(--cat-text, #1f2937);
}

.result { margin-top: var(--cat-gap-2xl, 24px); }
.state { padding: 32px 0; display: flex; justify-content: center; }
.empty { text-align: center; padding: 48px; color: var(--cat-muted-light, #9ca3af); }
</style>
