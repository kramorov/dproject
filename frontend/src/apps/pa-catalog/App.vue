<!-- pa-catalog/App.vue — единый каркас каталога ПП.
     У ПП нет готового списка артикулов (item материализуется из конфигурации),
     поэтому режимы «Инженерный подбор» и «Быстрый подбор» скрыты; вместо
     «товаров серии» (CatalogModelLine) показываем конфигуратор. -->
<template>
  <div class="app">
    <Breadcrumbs :items="breadcrumbs" @navigate="goToSection" />
    <CatalogActions :active="activeTab" :tabs="tabs" @section="goToSection" @wizard="goToWizard" @ai="goToAi" />
    <KeepAlive :key="cacheEpoch">
      <CatalogSection
        v-if="page === 'section'"
        :api="api" :labels="labels.section" :filters="constructionFilters"
        @select-series="goToBrand"
        @navigate="goToSection"
      />
      <PaActuatorConfigurator
        v-else-if="page === 'brand'"
        :api="api"
        :initial-model-line-id="idValue"
        :initial-model-line-item-id="preSelect?.modelLineItemId || null"
        :initial-variety="preSelect?.variety || null"
        :initial-options="preSelect?.options || {}"
        :title="labels.brand.title"
        :subtitle="labels.brand.subtitle"
        @add-to-cart="onAddToCart"
      />
      <PaWizard
        v-else-if="page === 'wizard'"
        :api="api"
        @navigate="goToSection"
      />
      <AiSelectionPage
        v-else-if="page === 'ai'"
        :equipment-code="eqCode"
        :labels="labels.ai"
        eq-name="Пневмоприводы"
        @navigate="goToSection"
      />
    </KeepAlive>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import Breadcrumbs from '@/shared/components/Breadcrumbs.vue'
import CatalogActions from '@/shared/components/catalog/CatalogActions.vue'
import CatalogSection from '@/shared/components/catalog/CatalogSection.vue'
import PaActuatorConfigurator from '@/shared/components/catalog/PaActuatorConfigurator.vue'
import PaWizard from '@/shared/components/catalog/PaWizard.vue'
import AiSelectionPage from '@/pages/AiSelectionPage.vue'
import { useCatalogRouter } from '@/shared/composables/useCatalogRouter.js'
import paApi from './api'

const api = paApi
const route = useRoute()
const equipmentTypeId = 3 // Пневмопривод
const eqCode = 'pneumatic-actuator'

// Скрываем «Инженерный подбор» и «Быстрый подбор»: для ПП нет готового
// списка моделей, типовой механизм этих подборов не работает.
const tabs = [
  { key: 'section', label: 'Просмотр по сериям', event: 'section' },
  { key: 'wizard', label: 'Мастер подбора', event: 'wizard' },
  { key: 'ai', label: 'AI подбор', event: 'ai' },
]

const labels = {
  section: { title: 'Пневмоприводы', subtitle: 'Выберите серию пневмопривода', breadcrumbName: 'Пневмоприводы' },
  brand: { title: 'Конфигуратор пневмопривода', subtitle: 'Серия → типоразмер → опции', breadcrumbName: 'Пневмоприводы' },
  wizard: { breadcrumbName: 'Пневмоприводы', wizardTitle: 'Мастер подбора пневмоприводов' },
  ai: { breadcrumbName: 'Пневмоприводы', aiTitle: 'AI подбор пневмоприводов' },
}

const cacheEpoch = ref(0)
// Предвыбор типоразмера/вида при открытии конфигуратора из мастера/селектора.
const preSelect = ref(null)
// Чипсы «Конструкция» для фильтра серий (по умолчанию шестерня-рейка).
const constructionFilters = ref([])

onMounted(async () => {
  try {
    const { data } = await api.getInitialData()
    const varieties = data?.construction_varieties || []
    if (!varieties.length) return
    const options = varieties.map(v => ({ value: v.id, label: v.name }))
    const rp = varieties.find(v => v.code === 'RACK-PINION' || v.code === 'RP')
      || varieties[0]
    constructionFilters.value = [
      { field: 'construction_variety_id', param: 'construction_variety_id', label: 'Конструкция', options, default: rp.id },
    ]
  } catch (e) {
    console.error('[pa-catalog] construction filter load failed:', e)
  }
})
// У ПП нет каталоговых фильтров — не дёргаем getFilters().
const { page, idValue, goToBrand: _goToBrand } = useCatalogRouter(api, { idProp: 'model_line_id', preloadFilters: false })
const previousPage = ref('section')
const pageSubtitle = ref('')

const modeNames = { section: 'Просмотр по сериям', brand: 'Просмотр по сериям', wizard: 'Мастер подбора', ai: 'AI подбор' }
const parentModeName = computed(() => modeNames[page.value] || 'Просмотр по сериям')

const eqLabel = 'Пневмоприводы'
const breadcrumbs = computed(() => {
  const items = [{ name: 'Каталог', to: '/' }, { name: eqLabel }]
  const mode = parentModeName.value
  if (mode) items.push({ name: mode })
  if (pageSubtitle.value) items.push({ name: pageSubtitle.value })
  return items
})

const tabKeys = { section: 'section', brand: 'section', wizard: 'wizard', ai: 'ai' }
const activeTab = computed(() => tabKeys[page.value] || 'section')

function goToBrand(id) { preSelect.value = null; cacheEpoch.value++; _goToBrand(id) }
const OPTION_QUERY_KEYS = ['safety_position', 'exd', 'ip', 'hand_wheel', 'body_coating', 'body_material']
function openConfigurator(mlId, itemId, variety, options = {}) {
  preSelect.value = { modelLineItemId: itemId, variety, options }
  cacheEpoch.value++
  _goToBrand(mlId)
}
function goToWizard() { cacheEpoch.value++; previousPage.value = page.value; page.value = 'wizard' }
function goToAi() { previousPage.value = page.value; page.value = 'ai' }
function goToSection() { preSelect.value = null; cacheEpoch.value++; pageSubtitle.value = ''; previousPage.value = page.value; page.value = 'section' }

// Открытие конфигуратора по URL (мастер/селектор → /catalog/pa-actuators?model_line_id=&model_line_item_id=&variety=).
watch(() => route.query, (q) => {
  if (q.model_line_id) {
    const options = {}
    for (const k of OPTION_QUERY_KEYS) if (q[k]) options[k] = q[k]
    openConfigurator(
      Number(q.model_line_id),
      q.model_line_item_id ? Number(q.model_line_item_id) : null,
      q.variety || null,
      options,
    )
  }
}, { immediate: true })

async function onAddToCart(payload) {
  try {
    const { data } = await api.createSku(payload)
    alert(`Добавлено в корзину: ${data.code || data.name}`)
  } catch (e) {
    alert('Ошибка: ' + (e.response?.data?.error || e.message))
  }
}
</script>

<style scoped>
.app { max-width: 1200px; margin: 0 auto; }
</style>
