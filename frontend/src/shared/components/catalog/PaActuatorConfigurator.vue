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
      <div class="pa-top">
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

      <!-- 3. Количество пружин (под блоком «Модель») -->
      <div class="step" v-if="springsField">
        <div class="step-label">{{ springsField.label }}</div>
        <div class="chips">
          <button
            v-for="o in springsField.items"
            :key="o.id"
            class="chip"
            :class="{ active: form.springs_qty === o.id }"
            @click="toggleOption('springs_qty', o.id)"
          >{{ o.name }}{{ o.is_default ? ' (стандарт)' : '' }}</button>
        </div>
      </div>
      </div><!-- /.pa-top -->

      <div class="pa-body">
      <!-- 4. Остальные опции (сайдбар) -->
      <aside class="pa-sidebar" v-if="otherOptionFields.length || hasBodyDesign">
        <div class="step-label">Опции</div>
        <div class="option-groups">
          <div class="option-group" v-for="opt in otherOptionFields" :key="opt.key">
            <div class="option-label">{{ opt.label }}</div>
            <div class="chips">
              <button
                v-for="o in opt.items"
                :key="o.id"
                class="chip"
                :class="{ active: form[opt.key] === o.id }"
                @click="toggleOption(opt.key, o.id)"
              >{{ o.name }}{{ o.is_default ? ' (стандарт)' : '' }}</button>
            </div>
          </div>

          <!-- Исполнение корпуса: материал + покрытие — связанные чипсы.
               В данных это одна опция (PneumaticBodyDesignOption), но выбираем
               материал и покрытие как два независимых измерения и резолвим
               выбранную пару обратно в конкретную опцию серии. -->
          <template v-if="hasBodyDesign">
            <div class="option-group">
              <div class="option-label">Материал корпуса</div>
              <div class="chips">
                <button
                  v-for="m in bodyMaterials"
                  :key="m"
                  class="chip"
                  :class="{ active: form.body_material === m }"
                  @click="selectBodyMaterial(m)"
                >{{ m }}</button>
              </div>
            </div>
            <div class="option-group">
              <div class="option-label">Покрытие корпуса</div>
              <div class="chips">
                <button
                  v-for="c in bodyCoatings"
                  :key="c"
                  class="chip"
                  :class="{ active: form.body_coating_label === c }"
                  @click="selectBodyCoating(c)"
                >{{ c }}</button>
              </div>
            </div>
          </template>
        </div>
      </aside><!-- /.pa-sidebar -->

      <div class="pa-content">
      <!-- 5. Результат -->
      <div class="result" v-if="preview">
        <PaProductCard
          :preview="preview"
          @add-to-cart="$emit('addToCart', buildPayload())"
        />
      </div>
      <div v-else-if="loading" class="state"><Spinner /></div>
      </div><!-- /.pa-content -->
      </div><!-- /.pa-body -->
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import PageTitle from '@/shared/components/PageTitle.vue'
import Spinner from '@/shared/components/Spinner.vue'
import PaProductCard from './PaProductCard.vue'

const props = defineProps({
  api: { type: Object, required: true },
  title: { type: String, default: 'Конфигуратор пневмопривода' },
  subtitle: { type: String, default: 'Серия → типоразмер → опции' },
  // Предвыбор серии (из CatalogSection, единый паттерн)
  initialModelLineId: { type: Number, default: null },
  // Предвыбор типоразмера и вида (из мастера/селектора)
  initialModelLineItemId: { type: Number, default: null },
  initialVariety: { type: String, default: null },
  // Предвыбранные опции: { safety_position, exd, ip, hand_wheel, body_coating, body_material }
  initialOptions: { type: Object, default: () => ({}) },
})
defineEmits(['addToCart'])

const OPTION_KEY_MAP = {
  safety_positions: 'safety_position',
  springs_qty_options: 'springs_qty',
  temperature_options: 'temperature',
  ip_options: 'ip',
  exd_options: 'exd',
  hand_wheel_options: 'hand_wheel',
}

const OPTION_LABELS = {
  safety_position: 'Положение безопасности',
  springs_qty: 'Количество пружин',
  temperature: 'Температурное исполнение',
  ip: 'Степень защиты IP',
  exd: 'Взрывозащита',
  hand_wheel: 'Ручной дублёр',
}

const OPTION_KEYS = ['springs_qty', 'temperature', 'safety_position', 'ip', 'exd', 'body_coating', 'hand_wheel']

const modelLines = ref([])
const modelItems = ref([])
const optionFields = ref([])
const springsField = computed(() => optionFields.value.find(f => f.key === 'springs_qty') || null)
const otherOptionFields = computed(() => optionFields.value.filter(f => f.key !== 'springs_qty'))
const preview = ref(null)
const loadingML = ref(false)
const loading = ref(false)

// Исполнение корпуса (одна опция PneumaticBodyDesignOption = материал + покрытие + цвет + кодировка).
// Выбираем материал/покрытие как два измерения, резолвим пару обратно в option.id.
const bodyDesign = ref({ items: [] })
const bodyMaterials = computed(() => {
  const s = new Set()
  for (const o of bodyDesign.value.items) if (o.material) s.add(o.material)
  return [...s]
})
const bodyCoatings = computed(() => {
  const s = new Set()
  for (const o of bodyDesign.value.items) if (o.coating) s.add(o.coating)
  return [...s]
})
const hasBodyDesign = computed(() => bodyDesign.value.items.length > 0)

const form = reactive({
  model_line_id: null,
  variety: null,
  model_line_item_id: null,
  springs_qty: null, temperature: null, safety_position: null,
  ip: null, exd: null, body_coating: null, hand_wheel: null,
  body_material: null, body_coating_label: null,
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
    form.model_line_id = props.initialModelLineId
    resetAfter('model_line_id')
    if (props.initialVariety) {
      await selectVariety(props.initialVariety)
      if (props.initialModelLineItemId) {
        await selectItem(props.initialModelLineItemId)
      }
    } else {
      await autoSelectVariety()
    }
    applyInitialOptions()
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
  form.body_material = null
  form.body_coating_label = null
  bodyDesign.value = { items: [] }
  optionFields.value = []
  preview.value = null

  loading.value = true
  try {
    const { data } = await props.api.getOptions(id)
    const fields = []
    for (const [apiKey, items] of Object.entries(data || {})) {
      if (!Array.isArray(items) || !items.length) continue

      // Исполнение корпуса — особая опция (материал + покрытие).
      if (apiKey === 'body_coating_options') {
        const bd = items.map(o => ({
          id: o.option_id || o.id,
          material: o.material || '',
          coating: o.coating || '',
          is_default: o.is_default,
        }))
        bodyDesign.value = { items: bd }
        const def = bd.find(o => o.is_default) || bd[0]
        if (def) {
          form.body_material = def.material
          form.body_coating_label = def.coating
          form.body_coating = def.id
        }
        continue
      }

      const formKey = OPTION_KEY_MAP[apiKey]
      if (!formKey) continue
      const mapped = items.map(o => ({
        id: o.option_id || o.id,
        name: o.name,
        is_default: o.is_default,
      }))
      fields.push({ key: formKey, label: OPTION_LABELS[formKey] || formKey, items: mapped })
      // Единственная опция — выделяем по умолчанию; иначе — только is_default.
      if (form[formKey] === null) {
        if (mapped.length === 1) {
          form[formKey] = mapped[0].id
        } else {
          const def = mapped.find(o => o.is_default)
          if (def) form[formKey] = def.id
        }
      }
    }
    optionFields.value = fields
    await fetchPreview()
  } catch (e) {
    console.error('PaActuatorConfigurator: options failed', e)
  }
  loading.value = false
}

function toggleOption(key, value) {
  const v = Number(value)
  // Клик по активному чипсу снимает выбор (как в «Быстром подборе»).
  form[key] = form[key] === v ? null : v
  fetchPreview()
}

function selectBodyMaterial(material) {
  if (form.body_material === material) {
    clearBodyDesign()
    return
  }
  form.body_material = material
  const opts = bodyDesign.value.items.filter(o => o.material === material)
  // Покрытие не совместимо с новым материалом — автопереключаем.
  if (!opts.some(o => o.coating === form.body_coating_label)) {
    const def = opts.find(o => o.is_default) || opts[0]
    form.body_coating_label = def ? def.coating : null
  }
  resolveBodyOption()
  fetchPreview()
}

function selectBodyCoating(coating) {
  if (form.body_coating_label === coating) {
    clearBodyDesign()
    return
  }
  form.body_coating_label = coating
  const opts = bodyDesign.value.items.filter(o => o.coating === coating)
  // Материал не совместим с новым покрытием — автопереключаем.
  if (!opts.some(o => o.material === form.body_material)) {
    const def = opts.find(o => o.is_default) || opts[0]
    form.body_material = def ? def.material : null
  }
  resolveBodyOption()
  fetchPreview()
}

function resolveBodyOption() {
  const match = bodyDesign.value.items.find(
    o => o.material === form.body_material && o.coating === form.body_coating_label
  )
  form.body_coating = match ? match.id : null
}

function clearBodyDesign() {
  form.body_material = null
  form.body_coating_label = null
  form.body_coating = null
  fetchPreview()
}

function applyInitialOptions() {
  const o = props.initialOptions || {}
  let changed = false
  // Прямые опции (id реальных опций): safety_position, exd, ip, hand_wheel
  for (const key of ['safety_position', 'exd', 'ip', 'hand_wheel']) {
    if (o[key] == null || o[key] === '') continue
    const f = optionFields.value.find(x => x.key === key)
    if (!f) continue
    const hit = f.items.find(it => String(it.id) === String(o[key]))
    if (hit) { form[key] = hit.id; changed = true }
  }
  // Материал корпуса (по имени — form.body_material хранит имя)
  if (o.body_material != null && o.body_material !== '') {
    const m = String(o.body_material)
    if (bodyMaterials.value.includes(m)) {
      form.body_material = m
      const opts = bodyDesign.value.items.filter(b => b.material === m)
      if (!opts.some(b => b.coating === form.body_coating_label)) {
        const def = opts.find(b => b.is_default) || opts[0]
        form.body_coating_label = def ? def.coating : null
      }
      resolveBodyOption()
      changed = true
    }
  }
  // Покрытие (id PneumaticBodyDesignOption) — из селектора coating_id
  if (o.body_coating != null && o.body_coating !== '') {
    const bd = bodyDesign.value.items.find(b => String(b.id) === String(o.body_coating))
    if (bd) {
      form.body_material = bd.material
      form.body_coating_label = bd.coating
      form.body_coating = bd.id
      changed = true
    }
  }
  if (changed) fetchPreview()
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
  form.body_material = null
  form.body_coating_label = null
  bodyDesign.value = { items: [] }
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
.pa-config { max-width: 1400px; margin: 0 auto; padding: var(--cat-gap-lg, 16px); }
.step { margin-bottom: var(--cat-gap-xl, 20px); }
.step-label {
  font-weight: 600; font-size: var(--cat-text-sm, 13px); color: var(--cat-text-soft, #374151);
  margin: 10px 0 6px;
}
.pa-top { margin-bottom: var(--cat-gap-xl, 20px); }
.pa-body { display: flex; gap: 28px; align-items: flex-start; }
.pa-sidebar { width: 300px; flex-shrink: 0; }
.pa-content { flex: 1; min-width: 0; }

.chips { display: flex; flex-wrap: wrap; gap: var(--cat-gap-xs, 6px); }
.chip {
  padding: 6px 14px; font-size: var(--cat-text-sm, 13px);
  border: 1px solid var(--cat-border, #e5e7eb); border-radius: 18px;
  background: var(--cat-surface, #fff); color: var(--cat-text, #1f2937); cursor: pointer;
  transition: all .12s; white-space: nowrap;
}
.chip:hover { border-color: var(--cat-primary, #2563eb); color: var(--cat-primary, #2563eb); }
.chip.active { background: var(--cat-primary, #2563eb); color: #fff; border-color: var(--cat-primary, #2563eb); }

.pa-sidebar .chips { flex-direction: column; align-items: stretch; flex-wrap: nowrap; }
.pa-sidebar .chip {
  width: 100%; text-align: left; white-space: normal; word-break: break-word;
  border-radius: 10px; padding: 8px 12px;
}

.option-groups { display: flex; flex-direction: column; gap: var(--cat-gap-md, 12px); }
.option-label { font-size: var(--cat-text-xs, 12px); color: var(--cat-muted, #6b7280); margin-bottom: 4px; }

.result { margin-top: 0; }
.state { padding: 32px 0; display: flex; justify-content: center; }
.empty { text-align: center; padding: 48px; color: var(--cat-muted-light, #9ca3af); }

@media (max-width: 900px) {
  .pa-body { flex-direction: column; }
  .pa-sidebar { width: 100%; }
}
</style>
