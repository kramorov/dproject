<!-- pages/catalog/CatalogEquipmentIndex.vue — Каталоги оборудования -->
<template>
  <div class="cat-index">
    <Breadcrumbs :items="breadcrumbs" />
    <h1 class="cat-title">Каталоги оборудования</h1>
    <div class="cat-grid">
      <router-link v-for="cat in items" :key="cat.to" :to="cat.to" class="cat-card">
        <div class="cat-img">
          <img v-if="cat.img" :src="cat.img" :alt="cat.name" class="cat-pic" @error="$event.target.style.display='none'" />
        </div>
        <h3 class="cat-name">{{ cat.name }}</h3>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import Breadcrumbs from '@/shared/components/Breadcrumbs.vue'

function img(path) { return `${import.meta.env.BASE_URL}img/catalog/${path}` }

const breadcrumbs = [
  { name: 'Главная', to: '/' },
  { name: 'Каталоги оборудования' },
]

const items = [
  { to:'/catalog/pneumatic-fittings', name:'Пневмофитинги', img:img('pneumatic-fittings.webp') },
  { to:'/catalog/filter-regulator', name:'Фильтр-регуляторы', img:img('filter-regulator.webp') },
  { to:'/catalog/cable-glands', name:'Кабельные вводы', img:img('cable-glands.webp') },
  { to:'/catalog/pa-actuators', name:'Пневмоприводы', img:img('pa-actuators.webp') },
  { to:'/catalog/gearbox', name:'Ручные дублёры', img:img('gearbox.webp') },
  { to:'/catalog/ea-reducers', name:'Редукторы к ЭП', img:img('ea-reducers.webp') },
  { to:'/catalog/solenoid-valves', name:'Соленоидные клапаны', img:img('solenoid-valves.webp') },
  { to:'/catalog/positioners', name:'Позиционеры', img:img('positioners.webp') },
  { to:'/catalog/limit-switch', name:'БКВ', img:img('limit-switch.webp') },
  { to:'/catalog/ea-actuators', name:'Электроприводы', img:img('ea-actuators.webp') },
  { to:'/catalog/ea-cabinets', name:'Шкафы управления ЭП', img:img('ea-cabinets.webp') },
  { to:'/catalog/mounting-kits', name:'Монтажные комплекты', img:img('mounting-kits.webp') },
]
</script>

<style scoped>
.cat-index { max-width: 1000px; margin: 0 auto; }
.cat-title { font-size: 24px; font-weight: 700; color: #1f2937; margin: 0 0 24px; }
.cat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.cat-card { display: flex; flex-direction: column; padding: 0 0 16px; background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; text-decoration: none; transition: all .15s; overflow: hidden; }
.cat-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,.08); border-color: #2563eb; transform: translateY(-2px); }
.cat-img { height: 160px; display: flex; align-items: center; justify-content: center; margin-bottom: 8px; background: #f3f4f6; overflow: hidden; }
.cat-pic { width: 100%; height: 100%; object-fit: contain; }
.cat-name { font-size: 14px; font-weight: 600; color: #1f2937; margin: 0; padding: 0 12px; line-height: 1.3; text-align: center; }
</style>
