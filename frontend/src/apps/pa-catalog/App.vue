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
        :api="api" :labels="labels.section"
        @select-series="goToBrand"
        @navigate="goToSection"
      />
      <PaActuatorConfigurator
        v-else-if="page === 'brand'"
        :api="api"
        :initial-model-line-id="idValue"
        :title="labels.brand.title"
        :subtitle="labels.brand.subtitle"
        @add-to-cart="onAddToCart"
      />
      <WizardSelection
        v-else-if="page === 'wizard'"
        :equipment-type-id="equipmentTypeId"
        :labels="labels.wizard"
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
import { ref, computed } from 'vue'
import Breadcrumbs from '@/shared/components/Breadcrumbs.vue'
import CatalogActions from '@/shared/components/catalog/CatalogActions.vue'
import CatalogSection from '@/shared/components/catalog/CatalogSection.vue'
import PaActuatorConfigurator from '@/shared/components/catalog/PaActuatorConfigurator.vue'
import WizardSelection from '@/shared/components/catalog/WizardSelection.vue'
import AiSelectionPage from '@/pages/AiSelectionPage.vue'
import { useCatalogRouter } from '@/shared/composables/useCatalogRouter.js'
import paApi from './api'

const api = paApi
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

function goToBrand(id) { cacheEpoch.value++; _goToBrand(id) }
function goToWizard() { cacheEpoch.value++; previousPage.value = page.value; page.value = 'wizard' }
function goToAi() { previousPage.value = page.value; page.value = 'ai' }
function goToSection() { cacheEpoch.value++; pageSubtitle.value = ''; previousPage.value = page.value; page.value = 'section' }

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
