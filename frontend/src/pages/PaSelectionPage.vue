<!-- PaSelectionPage.vue — Подбор пневмопривода по моменту (/selector/pa).
     Панель фильтров — переиспользуемый PaFilterBar (общие стили с инженерным
     подбором /catalog/pa-actuators?mode=engineer). Отличие: поиск идёт по
     сериям/корпусам (/selector/search/) с переходом в конфигуратор по клику
     на карточку. -->
<template>
  <div class="pa-selector">
    <PageTitle :title="title" />
    <PaFilterBar
      ref="filterBar"
      v-model="form"
      :searching="searching"
      @search="onSearch"
      @search-error="onSearchError"
      @reset="onReset"
    />

    <div v-if="error" class="error-msg">❌ {{ error }}</div>

    <SelectionResultGrid
      :items="cards"
      :total="cards.length"
      :loading="searching"
      :results-label="t('catalog.common.found')"
      :empty-text="t('catalog.common.nothingFound')"
      @select="onSelectCard"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/shared/api'
import PageTitle from '@/shared/components/PageTitle.vue'
import SelectionResultGrid from '@/shared/components/catalog/SelectionResultGrid.vue'
import PaFilterBar from '@/shared/components/catalog/PaFilterBar.vue'
import { paResultsToCards, buildPaConfigQuery } from '@/shared/utils/paResults'
import { useI18n } from '@/shared/i18n'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const filterBar = ref(null)

function emptyForm() {
  return {
    valve_type_id: '', dn_id: '', pn_id: '',
    mounting_plate_id: '', stem_shape_id: '', stem_id: '',
    torque_without_safety: null, safety_factor: 1.5,
    model_line_id: '', model_line_item_id: null,
    construction_variety_id: '',
    actuator_variety_id: '', safety_position_id: '',
    air_pressure_id: '', ip_id: '', exd_id: '', exd_id_exact: '',
    coating_id: '', body_material_id: '', manual_override_id: '',
    temp_min: null, temp_max: null,
  }
}
const form = reactive(emptyForm())
const results = ref([])
const error = ref('')
const searching = ref(false)

const title = computed(() => t('pa.selector.title'))
const cards = computed(() => paResultsToCards(results.value, {
  series: t('pa.engineer.card.series'),
  body: t('pa.engineer.card.body'),
  type: t('pa.engineer.card.type'),
  margin: t('pa.engineer.card.margin'),
  nm: t('pa.engineer.card.nm'),
}))

async function onSearch(payload) {
  searching.value = true
  error.value = ''
  results.value = []

  try {
    const { data } = await api.post('/pneumatic_actuators/selector/search/', payload)
    results.value = data.search_results || []
    if (!results.value.length) error.value = t('catalog.common.nothingFound')
  } catch (e) {
    error.value = e.response?.data?.error || e.displayMessage || t('pa.engineer.errorGeneric')
  } finally {
    searching.value = false
  }
}

function onSearchError(msg) {
  error.value = msg
  results.value = []
  searching.value = false
}

function openProduct(item, ml, options = {}) {
  if (!item?.model_line_item_id) return
  router.push({ path: '/catalog/pa-actuators', query: buildPaConfigQuery(ml, item, options) })
}

function collectOptions(card) {
  const o = {}
  if (form.safety_position_id) o.safety_position = form.safety_position_id
  if (form.ip_id) o.ip = form.ip_id
  // Exd: в конфигуратор идёт точный вид (или одиночный id старого формата).
  if (form.exd_id_exact) o.exd = form.exd_id_exact
  else if (/^\d+$/.test(String(form.exd_id))) o.exd = form.exd_id
  if (form.manual_override_id) o.manual_override = form.manual_override_id
  // Материал корпуса — по имени (конфигуратор хранит имя), как в мастере.
  const mats = filterBar.value?.getBodyMaterialOptions() || []
  const mat = mats.find(m => m.id === form.body_material_id)
  if (mat) o.body_material = mat.name
  // Покрытие — id конкретного исполнения корпуса (аннотируется бэком в результат).
  const bdId = card?._ml?.body_design_option_id
  if (bdId) o.body_coating = bdId
  // Температура: диапазон из фильтров — конфигуратор выберет подходящий чипс.
  if (form.temp_min != null) o.temp_min = form.temp_min
  if (form.temp_max != null) o.temp_max = form.temp_max
  // Маркер происхождения — по нему конфигуратор показывает кнопку возврата.
  o.origin = 'pa-selector'
  return o
}

function onSelectCard(id) {
  const c = cards.value.find(x => x.id === id)
  if (!c) return
  // Сохраняем состояние фильтров/результатов для кнопки возврата из конфигуратора.
  try {
    sessionStorage.setItem('pa-selector-state', JSON.stringify({
      form: { ...form },
      results: results.value,
    }))
  } catch (e) { /* переполнение хранилища — не критично */ }
  openProduct(c._item, c._ml, collectOptions(c))
}

function onReset() {
  Object.assign(form, emptyForm())
  results.value = []
  error.value = ''
  try { sessionStorage.removeItem('pa-selector-state') } catch (e) { /* ignore */ }
}

onMounted(async () => {
  await filterBar.value?.init()

  // Возврат из конфигуратора (?restore=1): восстанавливаем фильтры и результаты,
  // чтобы не перенастраивать подбор для просмотра другой модели.
  if (route.query.restore === '1') {
    try {
      const raw = sessionStorage.getItem('pa-selector-state')
      if (raw) {
        const s = JSON.parse(raw)
        if (s.form) {
          await filterBar.value?.restore(s.form)
          results.value = s.results || []
        }
      }
    } catch (e) { /* повреждённое состояние — игнорируем */ }
    router.replace({ path: route.path, query: {} })
  }
})
</script>

<style scoped>
.pa-selector { max-width: 1200px; margin: 0 auto; padding: var(--cat-gap-xl, 16px); }
.error-msg { background: #fee; color: #c00; padding: 10px 16px; border-radius: 6px; margin: 12px 0; }
</style>
