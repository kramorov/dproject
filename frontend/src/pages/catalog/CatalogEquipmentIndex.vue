<!-- pages/catalog/CatalogEquipmentIndex.vue — Каталоги оборудования -->
<template>
  <div class="cat-index">
    <Breadcrumbs :items="breadcrumbs"/>
    <h1 class="cat-title">{{ t('menu.catalogEquipment') }}</h1>
    <div class="cat-grid">
      <router-link v-for="cat in items" :key="cat.to" :to="localizedPath(cat.to, locale)" class="cat-card">
        <div class="cat-img">
          <img v-if="cat.img" :src="cat.img" :alt="t(cat.nameKey)" class="cat-pic"
               @error="$event.target.style.display='none'"/>
        </div>
        <h3 class="cat-name">{{ t(cat.nameKey) }}</h3>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Breadcrumbs from '@/shared/components/Breadcrumbs.vue'
import { useI18n, localizedPath } from '@/shared/i18n'

const { locale, t } = useI18n()

function img(path) {
  return `${import.meta.env.BASE_URL}img/catalog/${path}`
}

const breadcrumbs = computed(() => [
  { name: t('breadcrumb.home'), to: localizedPath('/', locale.value) },
  { name: t('menu.catalogEquipment') },
])

const items = [
  { to: '/catalog/limit-switch', nameKey: 'catalog.name.limitSwitch', img: img('limit-switch.webp') },
  { to: '/catalog/solenoid-valves', nameKey: 'catalog.name.solenoidValves', img: img('solenoid-valves.webp') },
  { to: '/catalog/pa-actuators', nameKey: 'catalog.name.paActuators', img: img('pa-actuators.webp') },
  { to: '/catalog/gearbox', nameKey: 'catalog.name.gearbox', img: img('gearbox.webp') },
  { to: '/catalog/pneumatic-fittings', nameKey: 'catalog.name.pneumaticFittings', img: img('pneumatic-fittings.webp') },
  { to: '/catalog/pneumatic-silencers', nameKey: 'catalog.name.pneumaticSilencers', img: img('silencer_card_400.webp') },
  { to: '/catalog/pneumatic-plugs', nameKey: 'catalog.name.pneumaticPlugs', img: img('plug_card_400.webp') },
  { to: '/catalog/filter-regulator', nameKey: 'catalog.name.filterRegulator', img: img('filter-regulator.webp') },
  { to: '/catalog/cable-glands', nameKey: 'catalog.name.cableGlands', img: img('cable-glands.webp') },
  { to: '/catalog/ea-reducers', nameKey: 'catalog.name.eaReducers', img: img('ea-reducers.webp') },
  { to: '/catalog/positioners', nameKey: 'catalog.name.positioners', img: img('positioners.webp') },
  { to: '/catalog/ea-actuators', nameKey: 'catalog.name.eaActuators', img: img('ea-actuators.webp') },
  { to: '/catalog/ea-cabinets', nameKey: 'catalog.name.eaCabinets', img: img('ea-cabinets.webp') },
  { to: '/catalog/mounting-kits', nameKey: 'catalog.name.mountingKits', img: img('mounting-kits.webp') },
]
</script>

<style scoped>
.cat-index {
  max-width: 1000px;
  margin: 0 auto;
}

.cat-title {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 24px;
}

.cat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.cat-card {
  display: flex;
  flex-direction: column;
  padding: 0 0 16px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  text-decoration: none;
  transition: all .15s;
  overflow: hidden;
}

.cat-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, .08);
  border-color: #2563eb;
  transform: translateY(-2px);
}

.cat-img {
  height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
  background: #f3f4f6;
  overflow: hidden;
}

.cat-pic {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.cat-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  padding: 0 12px;
  line-height: 1.3;
  text-align: center;
}
</style>
