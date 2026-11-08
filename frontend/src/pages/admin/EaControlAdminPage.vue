<template>
  <div class="ec-admin">
    <h2>Блоки управления ЭП — настройка (ea_control)</h2>
    <div class="sections">
      <button v-for="s in SECTIONS" :key="s.key"
              :class="{ active: section === s.key }"
              @click="selectSection(s.key)">{{ s.label }}</button>
    </div>

    <div v-if="section === 'configurator'">
      <EaControlStructure />
    </div>

    <div v-else-if="section === 'preview'">
      <EaControlConfigurator />
    </div>

    <div v-else-if="section === 'description'">
      <EaControlDescription />
    </div>

    <div v-else-if="section === 'emulation'">
      <CuEmulationPage />
    </div>

    <div v-else-if="section === 'dicts'" class="split-layout">
      <!-- ЛЕВАЯ ЧАСТЬ: список справочников -->
      <div class="left-pane">
        <div class="pane-head">
          <h3>Справочники</h3>
        </div>
        <div class="model-list">
          <div v-for="m in models" :key="m.endpoint" class="model-item"
               :class="{ active: m.endpoint === current.endpoint }"
               @click="selectModel(m)">
            <span class="label">{{ m.label }}</span>
            <span class="code">{{ m.endpoint }}</span>
          </div>
        </div>
      </div>

      <!-- ПРАВАЯ ЧАСТЬ: общий CRUD-редактор справочника -->
      <div class="right-pane">
        <DictEditor ref="dictEditor" :config="current" :options-map="optionsMap"
                    variant="inline" />
      </div>
    </div>

    <template v-else>
      <div class="tabs">
        <button :class="{ active: buTab === 'units' }" @click="selectBuUnits()">Блоки управления</button>
        <button v-for="m in models" :key="m.endpoint"
                :class="{ active: buTab !== 'units' && m.endpoint === current.endpoint }"
                @click="selectBuModel(m)">{{ m.label }}</button>
      </div>

      <div v-if="buTab === 'units'">
        <EaControlUnitsEditor />
      </div>

      <DictEditor v-else ref="buEditor" :key="current.endpoint" :config="current"
                  :options-map="optionsMap" variant="modal" />
    </template>
  </div>
</template>

<script setup>
/**
 * Админка ea_control: CRUD всех моделей приложения через /api/ea-control/.
 *
 * Модель редактируемой сущности описывается конфигом MODEL_CONFIGS
 * (endpoint, заголовок, колонки таблицы и поля формы). Списки и формы —
 * общий компонент DictEditor (inline-форма для «Справочников», модалка для
 * «Редактора БУ»); поля — общий FieldInput; кнопки — общий EditorActions.
 * Выборы подгружаются с API — админке не нужно знать схему бэкенда.
 */
import { computed, onMounted, reactive, ref } from 'vue'
import api from '@/shared/api'
import EaControlStructure from './EaControlStructure.vue'
import EaControlConfigurator from './EaControlConfigurator.vue'
import EaControlDescription from './EaControlDescription.vue'
import CuEmulationPage from './CuEmulationPage.vue'
import EaControlUnitsEditor from './EaControlUnitsEditor.vue'
import DictEditor from '@/components/admin/DictEditor.vue'

const DICT_SOURCES = {
  'heater-supplies': 'Обогрев',
  'location-options': 'Размещение',
  'capabilities': 'Функции БУ',
  'control-logics': 'Логики работы',
  'local-control-types': 'Вид органов местного управления',
  'display-types': 'Вид отображения информации',
  'unit-power-sources': 'Питание БУ',
  'polarities': 'Полярность входных цепей',
  'control-unit-kinds': 'Классы БУ',
  'signal-form-categories': 'Категории форм сигналов',
  'control-signal-roles': 'Роли командных сигналов',
  'feedback-signal-roles': 'Роли сигналов ОС',
  'contact-normals': 'Норма контакта',
  'protocol-transports': 'Транспорты протоколов',
  'feedback-device-kinds': 'Категории устройств ОС',
  'feedback-technologies': 'Технологии устройств ОС',
  'access-device-options': 'Устройства ограничения доступа',
}

const F = (name, label, type = 'text', extra = {}) => ({ name, label, type, ...extra })

const MODEL_CONFIGS = [
  {
    endpoint: 'matrix-entries', label: 'Матрица', section: 'bu',
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
    endpoint: 'slot-rules', label: 'Правила', section: 'bu',
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
  {
    endpoint: 'control-signal-forms', label: 'Формы управляющих сигналов', section: 'dicts',
    columns: ['code', 'name', 'category', 'sorting_order', 'is_active'],
    fields: [
      F('code', 'Код'), F('name', 'Название'),
      F('category', 'Категория', 'select', { source: 'signal-form-categories' }),
      F('description', 'Описание', 'textarea'),
      F('sorting_order', 'Сортировка', 'number'), F('is_active', 'Активно', 'bool'),
    ],
  },
  {
    endpoint: 'feedback-signal-forms', label: 'Формы сигналов ОС', section: 'dicts',
    columns: ['code', 'name', 'category', 'sorting_order', 'is_active'],
    fields: [
      F('code', 'Код'), F('name', 'Название'),
      F('category', 'Категория', 'select', { source: 'signal-form-categories' }),
      F('description', 'Описание', 'textarea'),
      F('sorting_order', 'Сортировка', 'number'), F('is_active', 'Активно', 'bool'),
    ],
  },
  {
    endpoint: 'control-signals', label: 'Командные сигналы', section: 'dicts',
    columns: ['code', 'name', 'role', 'category', 'form', 'sorting_order', 'is_active'],
    fields: [
      F('code', 'Код'), F('name', 'Название'),
      F('role', 'Роль', 'select', { source: 'control-signal-roles' }),
      F('category', 'Категория', 'select', { choices: [
        ['discrete', 'Дискретный'], ['analog', 'Аналоговый']] }),
      F('form', 'Форма', 'select', { source: 'control-signal-forms' }),
      F('current', 'Ток входа, мА', 'number', { nullable: true }),
      F('wires', 'Проводов на канал', 'number', { nullable: true }),
      F('hart', 'HART', 'bool'),
      F('description', 'Описание', 'textarea'),
      F('sorting_order', 'Сортировка', 'number'), F('is_active', 'Активно', 'bool'),
    ],
  },
  {
    endpoint: 'feedback-signals', label: 'Сигналы ОС', section: 'dicts',
    columns: ['code', 'name', 'role', 'category', 'form', 'sorting_order', 'is_active'],
    fields: [
      F('code', 'Код'), F('name', 'Название'),
      F('role', 'Роль', 'select', { source: 'feedback-signal-roles' }),
      F('category', 'Категория', 'select', { choices: [
        ['contact', 'Контакт'], ['analog', 'Аналоговый']] }),
      F('form', 'Форма', 'select', { source: 'feedback-signal-forms' }),
      F('contact_normal', 'Норма контакта', 'select', { source: 'contact-normals' }),
      F('max_voltage', 'Макс. напряжение, В', 'number', { nullable: true }),
      F('max_current', 'Макс. ток, А', 'number', { nullable: true }),
      F('resistance_kohm', 'Сопротивление, кОм', 'number', { nullable: true }),
      F('max_power_w', 'Мощность, Вт', 'number', { nullable: true }),
      F('turns', 'Обороты', 'number', { nullable: true }),
      F('wires', 'Проводов на канал', 'number', { nullable: true }),
      F('hart', 'HART', 'bool'),
      F('description', 'Описание', 'textarea'),
      F('sorting_order', 'Сортировка', 'number'), F('is_active', 'Активно', 'bool'),
    ],
  },
  {
    endpoint: 'comm-protocols', label: 'Протоколы', section: 'dicts',
    columns: ['code', 'name', 'transport', 'sorting_order', 'is_active'],
    fields: [
      F('code', 'Код'), F('name', 'Название'),
      F('transport', 'Транспорт', 'select', { source: 'protocol-transports' }),
      F('description', 'Описание', 'textarea'),
      F('sorting_order', 'Сортировка', 'number'), F('is_active', 'Активно', 'bool'),
    ],
  },
  {
    endpoint: 'feedback-devices', label: 'Устройства ОС', section: 'dicts',
    columns: ['code', 'name', 'kind', 'technology', 'sorting_order', 'is_active'],
    fields: [
      F('code', 'Код'), F('name', 'Название'),
      F('kind', 'Категория', 'select', { source: 'feedback-device-kinds' }),
      F('technology', 'Технология', 'select', { source: 'feedback-technologies' }),
      F('contactless', 'Бесконтактный', 'bool'),
      F('accuracy', 'Точность'), F('life_cycles', 'Ресурс, циклов'),
      F('temp_range', 'Рабочая температура'),
      F('description', 'Описание', 'textarea'),
      F('sorting_order', 'Сортировка', 'number'), F('is_active', 'Активно', 'bool'),
    ],
  },
  {
    endpoint: 'signal-power-sources', label: 'Источники питания цепей', section: 'dicts',
    columns: ['code', 'name', 'internal', 'sorting_order', 'is_active'],
    fields: [
      F('code', 'Код'), F('name', 'Название'),
      F('internal', 'Встроенный (выдаёт опорное напряжение)', 'bool'),
      F('description', 'Описание', 'textarea'),
      F('sorting_order', 'Сортировка', 'number'), F('is_active', 'Активно', 'bool'),
    ],
  },
  {
    endpoint: 'signal-powers', label: 'Схемы цепей управления', section: 'dicts',
    columns: ['name', 'source', 'power_supply', 'input_form', 'polarity',
              'sorting_order', 'is_active'],
    fields: [
      F('name', 'Название'),
      F('source', 'Источник', 'select', { source: 'signal-power-sources' }),
      F('power_supply', 'Напряжение', 'select', { source: 'power_supplies' }),
      F('input_form', 'Форма входных цепей', 'select', { source: 'control-signal-forms' }),
      F('polarity', 'Полярность', 'select', { source: 'polarities' }),
      F('description', 'Описание', 'textarea'),
      F('sorting_order', 'Сортировка', 'number'), F('is_active', 'Активно', 'bool'),
    ],
  },
]
// справочники — одним конфигом
for (const [endpoint, label] of Object.entries(DICT_SOURCES)) {
  MODEL_CONFIGS.push({
    endpoint, label, section: 'dicts',
    columns: ['code', 'name', 'sorting_order', 'is_active'],
    fields: [
      F('code', 'Код'), F('name', 'Название'),
      F('description', 'Описание', 'textarea'),
      F('sorting_order', 'Сортировка', 'number'), F('is_active', 'Активно', 'bool'),
    ],
  })
}

const SECTIONS = [
  { key: 'configurator', label: 'Конфигуратор опций' },
  { key: 'bu', label: 'Редактор БУ' },
  { key: 'dicts', label: 'Справочники' },
  { key: 'preview', label: 'Превью БУ' },
  { key: 'description', label: 'Описание БУ' },
  { key: 'emulation', label: 'Тест фильтров' },
]

const section = ref('configurator')
const buTab = ref('units')
const models = computed(() => MODEL_CONFIGS.filter(m => m.section === section.value))
const current = ref(MODEL_CONFIGS[0])
const optionsMap = reactive({})
const dictEditor = ref(null)
const buEditor = ref(null)

function selectSection(key) {
  const ed = section.value === 'dicts' ? dictEditor.value
    : section.value === 'bu' ? buEditor.value : null
  if (ed && !ed.confirmUnsaved()) return
  section.value = key
  if (key === 'configurator' || key === 'preview' || key === 'description' || key === 'emulation') return
  const first = models.value[0]
  if (!first) return
  current.value = first
  if (key === 'bu') {
    buTab.value = 'units'
    return
  }
}

function selectModel(m) {
  if (dictEditor.value && !dictEditor.value.confirmUnsaved()) return
  current.value = m
}

function selectBuUnits() {
  if (buEditor.value && !buEditor.value.confirmUnsaved()) return
  buTab.value = 'units'
}

function selectBuModel(m) {
  if (buEditor.value && !buEditor.value.confirmUnsaved()) return
  buTab.value = m.endpoint
  current.value = m
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
})
</script>

<style scoped>
.ec-admin { padding: 16px; max-width: 1400px; }
.sections { display: flex; gap: 4px; margin-bottom: 8px; }
.sections button { padding: 8px 16px; border: 1px solid #ccc; background: #f5f5f5; cursor: pointer; font-weight: 600; }
.sections button.active { background: #2c6fb0; color: #fff; border-color: #2c6fb0; }
.tabs { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 12px; }
.tabs button { padding: 6px 10px; border: 1px solid #ccc; background: #f5f5f5; cursor: pointer; }
.tabs button.active { background: #2c6fb0; color: #fff; border-color: #2c6fb0; }

/* Справочники: слева список справочников, справа таблица значений */
.split-layout { display: flex; height: calc(100vh - 80px); border: 1px solid #ddd; border-radius: 4px; overflow: hidden; }
.split-layout .left-pane { width: 280px; flex-shrink: 0; border-right: 1px solid #ddd; overflow: auto; padding: 12px; }
.split-layout .right-pane { flex: 1; overflow: auto; padding: 12px; }
.pane-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.pane-head h3 { margin: 0; font-size: 18px; }
.model-list { display: flex; flex-direction: column; gap: 2px; }
.model-item { display: flex; gap: 6px; padding: 6px 8px; cursor: pointer; border-radius: 3px; }
.model-item:hover { background: #f0f0f0; }
.model-item.active { background: #2c6fb0; color: #fff; }
.model-item .label { flex: 1; }
.model-item .code { color: #888; font-size: 11px; }
.model-item.active .code { color: #dbe7f3; }
</style>
