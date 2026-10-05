<!-- pa-catalog/App.vue — единый каркас каталога ПП.
     У ПП нет готового списка артикулов (item материализуется из конфигурации),
     поэтому режимы «Инженерный подбор» и «Быстрый подбор» скрыты; вместо
     «товаров серии» (CatalogModelLine) показываем конфигуратор. -->
<template>
  <div class="app">
    <Breadcrumbs :items="breadcrumbs" @navigate="onNavigate" />
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
import { useCatalogRoute } from '@/shared/composables/useCatalogRoute.js'
import { useI18n } from '@/shared/i18n'
import paApi from './api'

const api = paApi
const route = useRoute()
const equipmentTypeId = 3 // Пневмопривод
const eqCode = 'pneumatic-actuator'

const tabs = [
  { key: 'section', label: 'catalog.mode.section', event: 'section' },
  { key: 'wizard', label: 'catalog.mode.wizard', event: 'wizard' },
  { key: 'ai', label: 'catalog.mode.ai', event: 'ai' },
]

const labels = {
  section: { title: 'Пневмоприводы', subtitle: 'Выберите серию пневмопривода', breadcrumbName: 'Пневмоприводы' },
  brand: { title: 'Конфигуратор пневмопривода', subtitle: 'Серия → типоразмер → опции', breadcrumbName: 'Пневмоприводы' },
  wizard: { breadcrumbName: 'Пневмоприводы', wizardTitle: 'Мастер подбора пневмоприводов' },
  ai: { breadcrumbName: 'Пневмоприводы', aiTitle: 'AI подбор пневмоприводов' },
}

const cacheEpoch = ref(0)
const preSelect = ref(null)
const constructionFilters = ref([])

const {
  page, idValue, router,
  goToSection: navSection, goToBrand: navBrand, goToWizard: navWizard, goToAi: navAi,
} = useCatalogRoute({ mlParam: 'model_line_id' })
const pageSubtitle = ref('')
const { t } = useI18n()

const modeNames = computed(() => ({
  section: t('catalog.mode.section'),
  brand: t('catalog.mode.section'),
  wizard: t('catalog.mode.wizard'),
  ai: t('catalog.mode.ai'),
}))
const parentModeName = computed(() => modeNames.value[page.value] || t('catalog.mode.section'))

const eqLabel = 'Пневмоприводы'
const breadcrumbs = computed(() => {
  const items = [
    { name: t('breadcrumb.catalog'), target: 'catalog-index' },
    { name: eqLabel, target: 'section' },
  ]
  if (page.value === 'brand') {
    items.push({ name: t('catalog.mode.section'), target: 'section' })
  } else {
    const current = modeNames.value[page.value]
    if (current && page.value !== 'section') items.push({ name: current })
  }
  if (pageSubtitle.value) items.push({ name: pageSubtitle.value })
  return items
})

const tabKeys = { section: 'section', brand: 'section', wizard: 'wizard', ai: 'ai' }
const activeTab = computed(() => tabKeys[page.value] || 'section')

function goToBrand(id) { preSelect.value = null; cacheEpoch.value++; navBrand(id) }
function goToWizard() { cacheEpoch.value++; navWizard() }
function goToAi() { navAi() }
function goToSection() { preSelect.value = null; cacheEpoch.value++; pageSubtitle.value = ''; navSection() }

function onNavigate(item) {
  const target = item?.target
  if (!target) return
  if (target === 'catalog-index') {
    if (router) router.push('/catalogs/equipment')
    else navSection()
    return
  }
  const map = { section: navSection, wizard: navWizard, ai: navAi }
  ;(map[target] || navSection)()
}

onMounted(async () => {
  try {
    const { data } = await api.getInitialData()
    const varieties = data?.construction_varieties || []
    if (!varieties.length) return
    const options = varieties.map(v => ({ value: v.id, label: v.name }))
    const rp = varieties.find(v => v.code === 'RACK-PINION' || v.code === 'RP') || varieties[0]
    constructionFilters.value = [
      { field: 'construction_variety_id', param: 'construction_variety_id', label: 'Конструкция', options, default: rp.id },
    ]
  } catch (e) {
    console.error('[pa-catalog] construction filter load failed:', e)
  }
})

const OPTION_QUERY_KEYS = ['safety_position', 'exd', 'ip', 'manual_override', 'body_coating', 'body_material']
// Предвыбор конфигуратора из URL (мастер/селектор → ?model_line_id=&model_line_item_id=&variety=...).
// Навигация уже обеспечена useCatalogRoute (ml=model_line_id → страница «brand»), здесь — только предвыбор.
watch(() => route.query, (q) => {
  const itemId = q.model_line_item_id ? Number(q.model_line_item_id) : null
  const variety = q.variety || null
  const options = {}
  for (const k of OPTION_QUERY_KEYS) if (q[k]) options[k] = q[k]
  preSelect.value = (itemId || variety || Object.keys(options).length)
    ? { modelLineItemId: itemId, variety, options }
    : null
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
