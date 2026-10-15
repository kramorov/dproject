<!-- shared/components/catalog/PaEngineerSelector.vue -->
<!-- Инженерный подбор пневмопривода по моменту (/catalog/pa-actuators?mode=engineer).
     Панель фильтров — переиспользуемый PaFilterBar (общие стили с /selector/pa).
     Результат — SKU-карточки с разделением точное/совместимое. -->
<template>
  <div class="pa-engineer">
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

    <div class="pa-engineer__results">
      <div class="pa-engineer__info">
        <span class="srg-spinner" v-if="searching" />
        <span v-else>{{ t('catalog.common.found') }} {{ cards.length }}</span>
      </div>

      <section v-if="exactCards.length" class="pa-engineer__section">
        <h3 v-if="compatibleCards.length" class="pa-engineer__section-title">{{ t('catalog.engineer.exactMatch') }} ({{ exactCards.length }})</h3>
        <div class="pa-engineer__grid">
          <PaEngineerGroupCard
            v-for="g in exactCards"
            :key="g.model_line_item_id || ('b' + g.body_id)"
            :group="g"
            @select="onSelectCard"
          />
        </div>
      </section>

      <section v-if="compatibleCards.length" class="pa-engineer__section">
        <h3 class="pa-engineer__section-title">{{ t('catalog.engineer.meetsConditions') }} ({{ compatibleCards.length }})</h3>
        <div class="pa-engineer__grid">
          <PaEngineerGroupCard
            v-for="g in compatibleCards"
            :key="'c-' + (g.model_line_item_id || ('b' + g.body_id))"
            :group="g"
            @select="onSelectCard"
          />
        </div>
      </section>

      <div v-if="!searching && !cards.length" class="pa-engineer__empty">{{ t('catalog.common.nothingFound') }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/shared/api'
import PageTitle from '@/shared/components/PageTitle.vue'
import PaFilterBar from '@/shared/components/catalog/PaFilterBar.vue'
import PaEngineerGroupCard from '@/shared/components/catalog/PaEngineerGroupCard.vue'
import { useI18n, localizedPath } from '@/shared/i18n'

const { t, locale } = useI18n()
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

const title = computed(() => t('pa.engineer.title'))
const cards = computed(() => results.value)
const exactCards = computed(() => cards.value.filter(c => c.is_exact))
const compatibleCards = computed(() => cards.value.filter(c => !c.is_exact))

async function onSearch(payload) {
  searching.value = true
  error.value = ''
  results.value = []

  try {
    const { data } = await api.post('/pneumatic_actuators/engineer/search/', payload)
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

function onSelectCard(skuId) {
  if (skuId) router.push(localizedPath(`/sku/${skuId}`, locale.value))
}

function onReset() {
  Object.assign(form, emptyForm())
  results.value = []
  error.value = ''
}

onMounted(async () => {
  await filterBar.value?.init()
})
</script>

<style scoped>
.pa-engineer { max-width: 1200px; margin: 0 auto; padding: var(--cat-gap-xl, 16px); }
.error-msg { background: #fee; color: #c00; padding: 10px 16px; border-radius: 6px; margin: 12px 0; }
.pa-engineer__info { font-size: var(--cat-text-base, 14px); color: var(--cat-muted, #6b7280); margin-bottom: 16px; }
.pa-engineer__section { margin-bottom: 32px; }
.pa-engineer__section-title { font-size: var(--cat-text-md, 16px); font-weight: 600; color: var(--cat-text, #1f2937); margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid var(--cat-border, #e5e7eb); }
.pa-engineer__grid { display: flex; flex-direction: column; gap: 12px; }
.pa-engineer__empty { text-align: center; padding: 60px 20px; color: var(--cat-muted-light, #9ca3af); font-size: var(--cat-text-lg, 16px); }
.srg-spinner { display: inline-block; width: 18px; height: 18px; border: 2px solid var(--cat-border, #e5e7eb); border-top-color: var(--cat-primary, #2563eb); border-radius: 50%; animation: srg-spin .6s linear infinite; }
@keyframes srg-spin { to { transform: rotate(360deg); } }
</style>
