<template>
  <div class="ec-admin">
    <h2>Блоки управления ЭП — настройка (ea_control)</h2>
    <div class="sections">
      <button v-for="s in SECTIONS" :key="s.key"
              :class="{ active: section === s.key }"
              @click="selectSection(s.key)">{{ s.label }}</button>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>

    <div v-if="section === 'configurator'">
      <EaControlStructure />
    </div>

    <div v-else-if="section === 'preview'">
      <EaControlConfigurator />
    </div>

    <div v-else-if="section === 'description'">
      <EaControlDescription />
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

      <!-- ПРАВАЯ ЧАСТЬ: сверху — значения справочника, ниже — редактирование -->
      <div class="right-pane">
        <div class="toolbar">
          <EditorActions align="start" :buttons="toolbarButtons" @action="onToolbarAction" />
          <span class="count">{{ rows.length }} записей</span>
        </div>

        <div class="table-scroll">
          <table v-if="rows.length" class="grid">
            <thead>
              <tr>
                <th v-for="c in columns" :key="c">{{ colLabel(c) }}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.id" class="row"
                  :class="{ editing: editing && editing.id === row.id }"
                  @click="onRowClick(row)">
                <td v-for="c in columns" :key="c">{{ display(row, c) }}</td>
                <td class="actions">
                  <button title="Удалить" @click.stop="remove(row)">✕</button>
                </td>
              </tr>
            </tbody>
          </table>
          <p v-else class="empty">Записей нет.</p>
        </div>

        <div v-if="editing" class="edit-area">
          <div class="edit-head">
            <h3>{{ editing.id ? 'Изменить' : 'Создать' }} — {{ current.label }}</h3>
            <EditorActions :buttons="editButtons" @action="onEditAction" />
          </div>
          <div v-if="deletePending" class="del-banner">Запись будет удалена при сохранении.</div>
          <div class="edit-form" @input="markDirty" @change="markDirty">
            <label v-for="f in current.fields" :key="f.name" class="edit-field"
                   :class="{ wide: isWide(f) }">
              <span>{{ f.label }}</span>
              <input v-if="f.type === 'text'" v-model="form[f.name]" />
              <textarea v-else-if="f.type === 'textarea'" v-model="form[f.name]" rows="2"></textarea>
              <input v-else-if="f.type === 'number'" type="number" v-model.number="form[f.name]" />
              <input v-else-if="f.type === 'bool'" type="checkbox" v-model="form[f.name]" />
              <select v-else-if="f.type === 'select'" v-model="form[f.name]">
                <option :value="null">— не задано —</option>
                <option v-for="o in selectOptions(f)" :key="o.id" :value="o.id">{{ o.label }}</option>
              </select>
            </label>
          </div>
        </div>
      </div>
    </div>

    <template v-else>
      <div class="tabs">
        <button :class="{ active: buTab === 'units' }" @click="buTab = 'units'">Блоки управления</button>
        <button v-for="m in models" :key="m.endpoint"
                :class="{ active: buTab !== 'units' && m.endpoint === current.endpoint }"
                @click="selectBuModel(m)">{{ m.label }}</button>
      </div>

      <div v-if="buTab === 'units'">
        <EaControlUnitsEditor />
      </div>

      <template v-else>
        <div class="toolbar">
          <EditorActions align="start" :buttons="toolbarButtons" @action="onToolbarAction" />
          <span class="count">{{ rows.length }} записей</span>
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
      </template>
    </template>

    <div v-if="editing && section === 'bu' && buTab !== 'units'" class="modal-backdrop" @click.self="editing = null">
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
                      :placeholder="`{'key': 'value'} или []`"></textarea>
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
          <EditorActions :buttons="modalButtons" @action="onModalAction" />
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
import EaControlStructure from './EaControlStructurePage.vue'
import EaControlConfigurator from './EaControlConfiguratorPage.vue'
import EaControlDescription from './EaControlDescription.vue'
import EaControlUnitsEditor from './EaControlUnitsEditor.vue'
import EditorActions from '@/components/EditorActions.vue'
import { t } from '@/shared/i18n'

const DICT_SOURCES = {
  'heater-supplies': 'Обогрев',
  'location-options': 'Размещение',
  'capabilities': 'Функции БУ',
  'control-logics': 'Логики работы',
  'local-control-types': 'Вид органов местного управления',
  'display-types': 'Вид отображения информации',
  'unit-power-sources': 'Питание БУ',
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
      F('category', 'Категория', 'select', { choices: [
        ['dry_input', 'Сухой контакт (внутренний опрос БУ)'],
        ['voltage_ac', 'Потенциал AC'], ['voltage_dc', 'Потенциал DC'],
        ['current_4_20', 'Токовая петля 4–20 мА']] }),
      F('description', 'Описание', 'textarea'),
      F('sorting_order', 'Сортировка', 'number'), F('is_active', 'Активно', 'bool'),
    ],
  },
  {
    endpoint: 'feedback-signal-forms', label: 'Формы сигналов ОС', section: 'dicts',
    columns: ['code', 'name', 'category', 'sorting_order', 'is_active'],
    fields: [
      F('code', 'Код'), F('name', 'Название'),
      F('category', 'Категория', 'select', { choices: [
        ['dry_output', 'Сухой контакт (выход реле)'],
        ['current_4_20', 'Токовая петля 4–20 мА'],
        ['resistance', 'Сопротивление (потенциометр)']] }),
      F('description', 'Описание', 'textarea'),
      F('sorting_order', 'Сортировка', 'number'), F('is_active', 'Активно', 'bool'),
    ],
  },
  {
    endpoint: 'control-signals', label: 'Командные сигналы', section: 'dicts',
    columns: ['code', 'name', 'role', 'category', 'form', 'sorting_order', 'is_active'],
    fields: [
      F('code', 'Код'), F('name', 'Название'),
      F('role', 'Роль', 'select', { choices: [
        ['CMD_OCS', 'О/С/З'], ['CMD_REMOTE', 'Дистанционное упр.'],
        ['CMD_LOCK', 'Блокировка'], ['CMD_MANUAL_OVERRIDE', 'Ручное дублирование'],
        ['CMD_4_20MA', 'Уставка 4–20 мА'], ['CMD_0_10V', 'Уставка 0–10 В'],
        ['CMD_EMERGENCY_OPEN', 'Аварийное «Открыть»'], ['CMD_EMERGENCY_CLOSE', 'Аварийное «Закрыть»'],
        ['MODE', 'Переключение режима'], ['INTERLOCK_OPEN', 'Блокировка «Открыть»'],
        ['INTERLOCK_CLOSE', 'Блокировка «Закрыть»'], ['DRIVE_ENABLE', 'Разрешение хода']] }),
      F('category', 'Категория', 'select', { choices: [
        ['discrete', 'Дискретный'], ['analog', 'Аналоговый']] }),
      F('form', 'Форма', 'select', { source: 'control-signal-forms' }),
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
      F('role', 'Роль', 'select', { choices: [
        ['END_OPEN', 'Конечное «Открыто»'], ['END_CLOSE', 'Конечное «Закрыто»'],
        ['WAY_OPEN', 'Промежуточное (открытие)'], ['WAY_CLOSE', 'Промежуточное (закрытие)'],
        ['TORQUE_OPEN', 'Моментный «Открыто»'], ['TORQUE_CLOSE', 'Моментный «Закрыто»'],
        ['POSITION', 'Положение (аналог)'], ['OVERHEAT', 'Перегрев'],
        ['TURN_COUNTER', 'Счётчик оборотов'], ['ALARM', 'Авария'], ['READY', 'Готовность'],
        ['TORQUE_ANALOG', 'Аналоговый момент'], ['STOP', 'Останов'],
        ['LOCAL_REMOTE', 'Местное/удалённое'], ['SELECTOR_POSITION', 'Положение селектора'],
        ['PHASE_LOSS', 'Потеря фазы']] }),
      F('category', 'Категория', 'select', { choices: [
        ['contact', 'Контакт'], ['analog', 'Аналоговый']] }),
      F('form', 'Форма', 'select', { source: 'feedback-signal-forms' }),
      F('contact_normal', 'Норма контакта', 'select', { choices: [
        ['NO', 'NO'], ['NC', 'NC'], ['CHANGEOVER', 'Перекидной']] }),
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
      F('transport', 'Транспорт', 'select', { choices: [
        ['RS485', 'RS-485'], ['ETHERNET', 'Ethernet'], ['OTHER', 'Прочее']] }),
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
      F('polarity', 'Полярность', 'select', { choices: [
        ['PNP', 'PNP — плюс-управление (активный высокий)'],
        ['NPN', 'NPN — минус-управление (активный низкий)'],
        ['BIDIRECTIONAL', 'Двунаправленный (DC, любая полярность)'],
        ['NOT_APPLICABLE', 'Не применимо (AC или сухой контакт)']] }),
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
]

const section = ref('configurator')
const buTab = ref('units')
const models = computed(() => MODEL_CONFIGS.filter(m => m.section === section.value))
const current = ref(MODEL_CONFIGS[0])
const rows = ref([])
const loading = ref(false)
const error = ref('')
const editing = ref(null)
const form = reactive({})
const optionsMap = reactive({})
// Грязное состояние встроенной формы справочников и двухшаговое удаление
const dirty = ref(false)
const deletePending = ref(false)

const columns = computed(() => current.value.columns)

const editingDeleteLabel = computed(() =>
  (editing.value && editing.value.id == null) ? t('eaControl.cancelCreate') : t('eaControl.deleteValue'))

// Кнопки тулбара списка, встроенной формы и модалки — через общий EditorActions
const toolbarButtons = computed(() => [
  { key: 'create', label: t('eaControl.add'), kind: 'primary' },
  { key: 'refresh', label: t('eaControl.refresh'), disabled: loading.value },
])

const editButtons = computed(() => [
  { key: 'save', label: t('eaControl.save'), kind: 'primary',
    disabled: !(dirty.value || deletePending.value) },
  { key: 'delete', label: deletePending.value ? t('eaControl.cancelDelete') : editingDeleteLabel.value,
    kind: deletePending.value ? 'danger' : 'default' },
])

const modalButtons = computed(() => [
  { key: 'save', label: t('eaControl.save'), kind: 'primary' },
  { key: 'cancel', label: t('eaControl.cancel') },
])

function onToolbarAction(b) {
  if (b.key === 'create') openCreate()
  else if (b.key === 'refresh') load()
}

function onEditAction(b) {
  if (b.key === 'save') save()
  else if (b.key === 'delete') toggleDeleteEditing()
}

function onModalAction(b) {
  if (b.key === 'save') save()
  else if (b.key === 'cancel') editing.value = null
}

function colLabel(c) {
  const f = current.value.fields.find(x => x.name === c)
  return f ? f.label : c
}

function display(row, c) {
  const v = row[c]
  if (v === null || v === undefined || v === '') return ''
  if (typeof v === 'boolean') return v ? '✓' : ''
  const f = current.value.fields.find(x => x.name === c)
  if (f) {
    if (f.choices) {
      const o = f.choices.find(([id]) => id === v)
      if (o) return o[1]
    }
    if (f.source && optionsMap[f.source]) {
      const o = optionsMap[f.source].find(o => o.id === v)
      if (o) return o.label
    }
  }
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

// Поля, занимающие всю ширину встроенной формы справочников
function isWide(f) {
  return f.type === 'textarea' || f.type === 'json' || f.type === 'multiselect'
}

function markDirty() {
  dirty.value = true
}

// Есть несохранённые изменения — спросить подтверждение перед уходом
function confirmUnsaved() {
  if (!editing.value || !dirty.value) return true
  return confirm('Есть несохранённые изменения. Отменить их и переключиться?')
}

function onRowClick(row) {
  if (editing.value && editing.value.id === row.id) return
  if (!confirmUnsaved()) return
  openEdit(row)
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

function selectSection(key) {
  if (!confirmUnsaved()) return
  section.value = key
  editing.value = null
  deletePending.value = false
  dirty.value = false
  if (key === 'configurator' || key === 'preview' || key === 'description') return
  const first = models.value[0]
  if (!first) return
  current.value = first
  if (key === 'bu') {
    buTab.value = 'units'
    return
  }
  load()
}

function selectModel(m) {
  if (!confirmUnsaved()) return
  current.value = m
  editing.value = null
  deletePending.value = false
  dirty.value = false
  load()
}

function selectBuModel(m) {
  if (!confirmUnsaved()) return
  buTab.value = m.endpoint
  current.value = m
  editing.value = null
  deletePending.value = false
  dirty.value = false
  load()
}

function openCreate() {
  if (!confirmUnsaved()) return
  const f = {}
  for (const field of current.value.fields) {
    f[field.name] = field.type === 'bool' ? true
      : field.type === 'multiselect' ? [] : (field.type === 'json' ? '' : null)
  }
  editing.value = { id: null }
  deletePending.value = false
  dirty.value = false
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
  deletePending.value = false
  dirty.value = false
  Object.assign(form, f)
}

function toggleDeleteEditing() {
  if (!editing.value) return
  if (editing.value.id == null) {
    // новый (несохранённый) — сразу отменяем создание
    editing.value = null
    deletePending.value = false
    dirty.value = false
    return
  }
  deletePending.value = !deletePending.value
}

async function save() {
  error.value = ''
  // Двухшаговое удаление: «Сохранить» с пометкой удаления выполняет DELETE
  if (deletePending.value) {
    try {
      if (editing.value && editing.value.id) {
        await api.delete(`/ea-control/${current.value.endpoint}/${editing.value.id}/`)
      }
      editing.value = null
      deletePending.value = false
      dirty.value = false
      await load()
    } catch (e) {
      error.value = e.displayMessage || 'Ошибка удаления'
    }
    return
  }
  const payload = {}
  for (const field of current.value.fields) {
    let v = form[field.name]
    if (field.type === 'json' && typeof v === 'string' && v.trim()) {
      try { v = JSON.parse(v) } catch { v = null }
    }
    if (v === '' || v === undefined) v = null
    // null=False поля DRF отклоняет («may not be null»): пустые скаляры
    // отправляем как '' / 0, а не null. select/json/multiselect не трогаем —
    // там null валиден (nullable-FK очищается) или поле обязано быть выбрано.
    if (v === null) {
      if (field.type === 'text' || field.type === 'textarea') v = ''
      else if (field.type === 'number') v = 0
    }
    payload[field.name] = v
  }
  try {
    if (editing.value && editing.value.id) {
      await api.put(`/ea-control/${current.value.endpoint}/${editing.value.id}/`, payload)
    } else {
      await api.post(`/ea-control/${current.value.endpoint}/`, payload)
    }
    editing.value = null
    deletePending.value = false
    dirty.value = false
    await load()
  } catch (e) {
    error.value = e.displayMessage || 'Ошибка сохранения'
  }
}

async function remove(row) {
  if (!confirm(`Удалить запись #${row.id}?`)) return
  try {
    await api.delete(`/ea-control/${current.value.endpoint}/${row.id}/`)
    if (editing.value && editing.value.id === row.id) {
      editing.value = null
      deletePending.value = false
      dirty.value = false
    }
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
})
</script>

<style scoped>
.ec-admin { padding: 16px; max-width: 1400px; }
.sections { display: flex; gap: 4px; margin-bottom: 8px; }
.sections button { padding: 8px 16px; border: 1px solid #ccc; background: #f5f5f5; cursor: pointer; font-weight: 600; }
.sections button.active { background: #2c6fb0; color: #fff; border-color: #2c6fb0; }
.error-banner { background: #fdecea; color: #c62828; padding: 8px 10px; border-radius: 4px; margin-bottom: 10px; }
.tabs { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 12px; }
.tabs button { padding: 6px 10px; border: 1px solid #ccc; background: #f5f5f5; cursor: pointer; }
.tabs button.active { background: #2c6fb0; color: #fff; border-color: #2c6fb0; }
.toolbar { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
.count { color: #666; }
.error { color: #c00; }
.empty { color: #999; }
.grid { width: 100%; border-collapse: collapse; font-size: 13px; }
.grid th, .grid td { border: 1px solid #ddd; padding: 4px 8px; text-align: left; }
.grid th { background: #f0f0f0; position: sticky; top: 0; }
.grid tbody tr.row { cursor: pointer; }
.grid tbody tr.row:hover { background: #f5f8fc; }
.grid tbody tr.row.editing { background: #e8f0fa; }
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

/* Прокрутка таблицы справочника (свыше ~10 строк) */
.table-scroll { overflow-y: auto; max-height: 320px; }
/* Встроенная форма редактирования значения */
.edit-area { border-top: 2px solid #2c6fb0; margin-top: 12px; padding-top: 10px; }
.edit-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.del-banner { background: #fdecea; color: #c62828; padding: 6px 8px; border-radius: 3px; margin-bottom: 8px; font-size: 13px; }
.edit-head h3 { margin: 0; font-size: 15px; }
.edit-form { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 12px; max-width: 760px; }
.edit-field { display: flex; align-items: center; gap: 8px; min-width: 0; }
.edit-field > span { flex: 0 0 110px; text-align: right; color: #444; font-size: 13px; }
.edit-field > input, .edit-field > select, .edit-field > textarea {
  flex: 1; min-width: 0; padding: 4px 6px; border: 1px solid #ccc; border-radius: 3px; box-sizing: border-box;
}
.edit-field > input[type='checkbox'] { flex: 0 0 auto; }
.edit-field.wide { grid-column: 1 / -1; }
</style>
