<template>
  <div class="ec-admin">
    <h2>Блоки управления ЭП — настройка (ea_control)</h2>
    <div class="tabs">
      <button v-for="m in models" :key="m.endpoint"
              :class="{ active: m.endpoint === current.endpoint }"
              @click="selectModel(m)">{{ m.label }}</button>
    </div>

    <div class="toolbar">
      <button @click="openCreate()">+ Добавить</button>
      <button @click="load" :disabled="loading">Обновить</button>
      <span class="count">{{ rows.length }} записей</span>
      <span v-if="error" class="error">{{ error }}</span>
    </div>

    <table v-if="rows.length" class="grid">
      <thead>
        <tr>
          <th v-for="c in columns" :key="c">{{ colLabel(c) }}</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.id">
          <td v-for="c in columns" :key="c">{{ display(row, c) }}</td>
          <td class="actions">
            <button title="Изменить" @click="openEdit(row)">✎</button>
            <button title="Удалить" @click="remove(row)">✕</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else class="empty">Записей нет.</p>

    <div v-if="editing" class="modal-backdrop" @click.self="editing = null">
      <div class="modal">
        <h3>{{ editing.id ? 'Изменить' : 'Создать' }} — {{ current.label }}</h3>
        <div class="form">
          <label v-for="f in current.fields" :key="f.name">
            <span>{{ f.label }}</span>
            <input v-if="f.type === 'text'" v-model="form[f.name]" />
            <textarea v-else-if="f.type === 'textarea'" v-model="form[f.name]" rows="3"></textarea>
            <input v-else-if="f.type === 'number'" type="number" v-model.number="form[f.name]" />
            <input v-else-if="f.type === 'bool'" type="checkbox" v-model="form[f.name]" />
            <textarea v-else-if="f.type === 'json'" v-model="form[f.name]" rows="4"
                      :placeholder="'{\"key\": \"value\"} или []'"></textarea>
            <select v-else-if="f.type === 'select'" v-model="form[f.name]">
              <option :value="null">— не задано —</option>
              <option v-for="o in selectOptions(f)" :key="o.id" :value="o.id">{{ o.label }}</option>
            </select>
            <div v-else-if="f.type === 'multiselect'" class="ms">
              <label v-for="o in selectOptions(f)" :key="o.id" class="ms-item">
                <input type="checkbox" :value="o.id"
                       :checked="(form[f.name] || []).includes(o.id)"
                       @change="toggleMs(f.name, o.id)" />
                {{ o.label }}
              </label>
            </div>
          </label>
        </div>
        <div class="modal-actions">
          <button @click="save">Сохранить</button>
          <button @click="editing = null">Отмена</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * Админка ea_control: CRUD всех моделей приложения через /api/ea-control/.
 *
 * Модель редактируемой сущности описывается конфигом MODEL_CONFIGS:
 * endpoint, заголовок, колонки таблицы и поля формы (тип, choices,
 * источник опций для select/multiselect). Выборы подгружаются с API —
 * админке не нужно знать схему бэкенда.
 */
import { computed, onMounted, reactive, ref } from 'vue'
import api from '@/shared/api'

const DICT_SOURCES = {
  'signal-forms': 'Формы сигналов',
  'control-signals': 'Командные сигналы',
  'feedback-signals': 'Сигналы ОС',
  'comm-protocols': 'Протоколы',
  'feedback-devices': 'Устройства ОС',
  'heater-supplies': 'Обогрев',
  'location-options': 'Размещение',
  'capabilities': 'Функции БУ',
  'signal-power-sources': 'Источники питания',
  'signal-powers': 'Питания цепей',
  'control-logics': 'Логики работы',
  'signal-types': 'Типы сигналов',
}

const F = (name, label, type = 'text', extra = {}) => ({ name, label, type, ...extra })

const MODEL_CONFIGS = [
  {
    endpoint: 'control-units', label: 'Блоки управления',
    columns: ['code', 'name', 'brand', 'kind', 'is_active'],
    fields: [
      F('brand', 'Бренд', 'select', { source: 'brands' }),
      F('code', 'Код'),
      F('name', 'Название'),
      F('kind', 'Класс БУ', 'select', { choices: [
        ['NONE', 'Без БУ'], ['BASIC', 'Базовый'], ['INTEGRATED', 'Интеллектуальный'],
        ['POSITIONER', 'Позиционер']] }),
      F('location', 'Размещение', 'select', { source: 'location-options' }),
      F('control_voltage', 'Напряжение цепей', 'select', { source: 'power_supplies' }),
      F('signal_power', 'Питание цепей', 'select', { source: 'signal-powers' }),
      F('accepts', 'Принимает команды', 'multiselect', { source: 'control-signals' }),
      F('emits', 'Выдаёт сигналы ОС', 'multiselect', { source: 'feedback-signals' }),
      F('protocols', 'Протоколы', 'multiselect', { source: 'comm-protocols' }),
      F('capabilities', 'Функции', 'multiselect', { source: 'capabilities' }),
      F('name_template', 'Шаблон названия', 'textarea'),
      F('description_template', 'Шаблон описания', 'textarea'),
      F('spec_template', 'Шаблон спецификации (JSON)', 'json'),
      F('description', 'Описание', 'textarea'),
      F('sorting_order', 'Сортировка', 'number'),
      F('is_active', 'Активно', 'bool'),
    ],
  },
  {
    endpoint: 'sections', label: 'Узлы-секции',
    columns: ['code', 'name', 'parent', 'sorting_order', 'is_active'],
    fields: [
      F('code', 'Код'), F('name', 'Название'),
      F('parent', 'Родитель', 'select', { source: 'sections' }),
      F('description', 'Описание', 'textarea'),
      F('sorting_order', 'Сортировка', 'number'), F('is_active', 'Активно', 'bool'),
    ],
  },
  {
    endpoint: 'slots', label: 'Слоты',
    columns: ['code', 'name', 'section', 'selection_mode', 'slot_kind', 'required', 'is_active'],
    fields: [
      F('code', 'Код'), F('name', 'Название'),
      F('section', 'Секция', 'select', { source: 'sections' }),
      F('selection_mode', 'Режим выбора', 'select', { choices: [
        ['single', 'Одиночный'], ['multi', 'Мульти'], ['xor', 'Взаимоисключающий'],
        ['bundle', 'Пакет']] }),
      F('slot_kind', 'Род значения', 'select', { choices: [
        ['value', 'Значение'], ['object', 'Объект'], ['subtype', 'Подтип']] }),
      F('required', 'Обязательный', 'bool'),
      F('description', 'Описание', 'textarea'),
      F('sorting_order', 'Сортировка', 'number'), F('is_active', 'Активно', 'bool'),
    ],
  },
  {
    endpoint: 'slot-options', label: 'Опции слотов',
    columns: ['code', 'name', 'slot', 'kind', 'encoding', 'ext_encoding', 'is_active'],
    fields: [
      F('code', 'Код'), F('name', 'Название'),
      F('slot', 'Слот', 'select', { source: 'slots' }),
      F('kind', 'Тип опции', 'select', { choices: [
        ['signal', 'Сигнал'], ['heater', 'Обогрев'], ['power', 'Питание цепей'],
        ['logic', 'Логика'], ['signal_type', 'Тип сигнала'], ['unit', 'БУ'],
        ['none', 'None-строка'], ['pair', 'Пара контактов']] }),
      F('control_signal', 'Командный сигнал', 'select', { source: 'control-signals' }),
      F('feedback_signal', 'Сигнал ОС', 'select', { source: 'feedback-signals' }),
      F('protocol', 'Протокол', 'select', { source: 'comm-protocols' }),
      F('heater_supply', 'Питание обогрева', 'select', { source: 'heater-supplies' }),
      F('signal_power', 'Питание цепей', 'select', { source: 'signal-powers' }),
      F('control_logic', 'Логика', 'select', { source: 'control-logics' }),
      F('signal_type', 'Тип сигнала', 'select', { source: 'signal-types' }),
      F('control_unit', 'БУ (kind=unit)', 'select', { source: 'units' }),
      F('device', 'Устройство', 'select', { source: 'feedback-devices' }),
      F('encoding', 'Кодировка'), F('ext_encoding', 'Ext-код'),
      F('description', 'Описание', 'textarea'),
      F('sorting_order', 'Сортировка', 'number'), F('is_active', 'Активно', 'bool'),
    ],
  },
  {
    endpoint: 'matrix-entries', label: 'Матрица',
    columns: ['slot', 'option', 'control_unit', 'power_supply', 'availability',
              'is_default', 'bundle', 'mode', 'encoding', 'ext_encoding'],
    fields: [
      F('slot', 'Слот', 'select', { source: 'slots' }),
      F('option', 'Опция', 'select', { source: 'slot-options' }),
      F('brand', 'Бренд (скоуп)', 'select', { source: 'brands' }),
      F('model_line', 'Серия (скоуп)', 'select', { source: 'model_lines' }),
      F('body', 'Корпус (скоуп)', 'select', { source: 'bodies' }),
      F('model_line_item', 'Модель (скоуп)', 'select', { source: 'model_line_items' }),
      F('control_unit', 'БУ (контекст)', 'select', { source: 'units' }),
      F('power_supply', 'Напряжение', 'select', { source: 'power_supplies' }),
      F('mode', 'Режим', 'select', { choices: [
        ['on_off', 'on-off'], ['modulating', 'Модулирующий'], ['both', 'Оба']] }),
      F('availability', 'Доступность', 'select', { choices: [
        ['std', 'Стандарт'], ['opt', 'Опция'], ['na', 'Недоступно']] }),
      F('is_default', 'По умолчанию', 'bool'),
      F('bundle', 'Пакет'),
      F('control_signal', 'Командный сигнал', 'select', { source: 'control-signals' }),
      F('feedback_signal', 'Сигнал ОС', 'select', { source: 'feedback-signals' }),
      F('protocol', 'Протокол', 'select', { source: 'comm-protocols' }),
      F('device', 'Устройство', 'select', { source: 'feedback-devices' }),
      F('heater_supply', 'Обогрев', 'select', { source: 'heater-supplies' }),
      F('encoding', 'Кодировка'), F('ext_encoding', 'Ext-код'),
      F('name', 'Название'), F('description', 'Описание', 'textarea'),
      F('sorting_order', 'Сортировка', 'number'),
    ],
  },
  {
    endpoint: 'slot-rules', label: 'Правила',
    columns: ['when_slot', 'when_operator', 'when_value', 'action', 'target_slot',
              'action_value', 'priority', 'is_active'],
    fields: [
      F('when_slot', 'Слот-условие', 'select', { source: 'slots' }),
      F('when_operator', 'Оператор', 'select', { choices: [
        ['exact', 'Равно'], ['not_exact', 'Не равно'], ['icontains', 'Содержит'],
        ['gte', 'Не меньше'], ['lte', 'Не больше'], ['in', 'В списке'],
        ['not_in', 'Не в списке'], ['is_set', 'Задано']] }),
      F('when_value', 'Значение условия (JSON)', 'json'),
      F('action', 'Действие', 'select', { choices: [
        ['show', 'Показать'], ['hide', 'Скрыть'], ['block', 'Заблокировать'],
        ['require', 'Обязать'], ['set_default', 'Дефолт']] }),
      F('target_slot', 'Слот-действие', 'select', { source: 'slots' }),
      F('action_value', 'Значение действия (JSON)', 'json'),
      F('priority', 'Приоритет', 'number'),
      F('description', 'Описание', 'textarea'),
      F('is_active', 'Активно', 'bool'),
    ],
  },
]
// справочники — одним конфигом
for (const [endpoint, label] of Object.entries(DICT_SOURCES)) {
  MODEL_CONFIGS.push({
    endpoint, label,
    columns: ['code', 'name', 'sorting_order', 'is_active'],
    fields: [
      F('code', 'Код'), F('name', 'Название'),
      F('description', 'Описание', 'textarea'),
      F('sorting_order', 'Сортировка', 'number'), F('is_active', 'Активно', 'bool'),
    ],
  })
}

const models = MODEL_CONFIGS
const current = ref(MODEL_CONFIGS[0])
const rows = ref([])
const loading = ref(false)
const error = ref('')
const editing = ref(null)
const form = reactive({})
const optionsMap = reactive({})

const columns = computed(() => current.value.columns)

function colLabel(c) {
  const f = current.value.fields.find(x => x.name === c)
  return f ? f.label : c
}

function display(row, c) {
  const v = row[c]
  if (v === null || v === undefined || v === '') return ''
  if (typeof v === 'boolean') return v ? '✓' : ''
  return String(v)
}

function selectOptions(f) {
  if (f.choices) {
    return f.choices.map(([id, label]) => ({ id, label }))
  }
  return optionsMap[f.source] || []
}

function toggleMs(name, id) {
  const arr = form[name] || []
  const i = arr.indexOf(id)
  if (i >= 0) arr.splice(i, 1)
  else arr.push(id)
  form[name] = arr
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get(`/ea-control/${current.value.endpoint}/`)
    rows.value = Array.isArray(data) ? data : data.results || []
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка загрузки'
  } finally {
    loading.value = false
  }
}

function selectModel(m) {
  current.value = m
  editing.value = null
  load()
}

function openCreate() {
  const f = {}
  for (const field of current.value.fields) {
    f[field.name] = field.type === 'bool' ? true
      : field.type === 'multiselect' ? [] : (field.type === 'json' ? '' : null)
  }
  editing.value = { id: null }
  Object.assign(form, f)
}

function openEdit(row) {
  const f = {}
  for (const field of current.value.fields) {
    let v = row[field.name]
    if (field.type === 'json' && v !== null && v !== undefined) {
      v = JSON.stringify(v, null, 2)
    }
    f[field.name] = v
  }
  editing.value = row
  Object.assign(form, f)
}

async function save() {
  error.value = ''
  const payload = {}
  for (const field of current.value.fields) {
    let v = form[field.name]
    if (field.type === 'json' && typeof v === 'string' && v.trim()) {
      try { v = JSON.parse(v) } catch { v = null }
    }
    if (v === '' || v === undefined) v = null
    payload[field.name] = v
  }
  try {
    if (editing.value && editing.value.id) {
      await api.put(`/ea-control/${current.value.endpoint}/${editing.value.id}/`, payload)
    } else {
      await api.post(`/ea-control/${current.value.endpoint}/`, payload)
    }
    editing.value = null
    await load()
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка сохранения'
  }
}

async function remove(row) {
  if (!confirm(`Удалить запись #${row.id}?`)) return
  try {
    await api.delete(`/ea-control/${current.value.endpoint}/${row.id}/`)
    await load()
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка удаления'
  }
}

async function loadOptions() {
  const sources = new Set()
  for (const m of MODEL_CONFIGS) {
    for (const f of m.fields) if (f.source) sources.add(f.source)
  }
  const requests = []
  for (const src of sources) {
    if (src === 'brands' || src === 'model_lines' || src === 'power_supplies'
        || src === 'bodies' || src === 'model_line_items') {
      requests.push(api.get('/ea-control/meta/').then(({ data }) => {
        for (const key of ['brands', 'model_lines', 'power_supplies',
                           'bodies', 'model_line_items']) {
          optionsMap[key] = (data[key] || []).map(o => ({
            id: o.id, label: o.code ? `${o.name} (${o.code})` : o.name }))
        }
      }))
    } else if (src === 'units') {
      requests.push(api.get('/ea-control/units/').then(({ data }) => {
        optionsMap.units = data.map(o => ({ id: o.id, label: `${o.name} (${o.code})` }))
      }))
    } else {
      requests.push(api.get(`/ea-control/${src}/`).then(({ data }) => {
        const list = Array.isArray(data) ? data : data.results || []
        optionsMap[src] = list.map(o => ({
          id: o.id, label: o.name || o.code || String(o.id) }))
      }))
    }
  }
  await Promise.all(requests)
}

onMounted(async () => {
  await loadOptions()
  await load()
})
</script>

<style scoped>
.ec-admin { padding: 16px; max-width: 1400px; }
.tabs { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 12px; }
.tabs button { padding: 6px 10px; border: 1px solid #ccc; background: #f5f5f5; cursor: pointer; }
.tabs button.active { background: #2c6fb0; color: #fff; border-color: #2c6fb0; }
.toolbar { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
.toolbar button { padding: 6px 12px; cursor: pointer; }
.count { color: #666; }
.error { color: #c00; }
.empty { color: #999; }
.grid { width: 100%; border-collapse: collapse; font-size: 13px; }
.grid th, .grid td { border: 1px solid #ddd; padding: 4px 8px; text-align: left; }
.grid th { background: #f0f0f0; position: sticky; top: 0; }
.actions { white-space: nowrap; }
.actions button { margin-right: 4px; cursor: pointer; }
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,.4);
  display: flex; align-items: flex-start; justify-content: center; padding-top: 40px; z-index: 100;
}
.modal { background: #fff; padding: 16px; width: 720px; max-height: 85vh; overflow: auto; border-radius: 6px; }
.form { display: grid; grid-template-columns: 1fr 2fr; gap: 8px 12px; align-items: center; }
.form label { display: contents; }
.form label span { text-align: right; color: #444; font-size: 13px; }
.form input, .form textarea, .form select {
  width: 100%; padding: 4px 6px; border: 1px solid #ccc; border-radius: 3px; box-sizing: border-box;
}
.ms { display: flex; flex-wrap: wrap; gap: 6px; max-height: 120px; overflow: auto; border: 1px solid #eee; padding: 4px; }
.ms-item { display: flex; gap: 4px; align-items: center; font-size: 13px; }
.modal-actions { margin-top: 14px; display: flex; gap: 8px; justify-content: flex-end; }
.modal-actions button { padding: 6px 14px; cursor: pointer; }
</style>
