<!-- pages/catalog/CatalogSolutionsIndex.vue — Каталог готовых решений -->
<template>
  <div class="cat-index">
    <Breadcrumbs :items="breadcrumbs" />
    <h1 class="cat-title">Каталог готовых решений</h1>
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
const breadcrumbs = [{ name: 'Главная', to: '/' }, { name: 'Каталог готовых решений' }]
const items = [
  { to:'/solutions/butterfly-ea', name:'Затворы дисковые с Электроприводами', img:img('solutions/butterfly-ea.webp') },
  { to:'/solutions/butterfly-pa', name:'Затворы дисковые с Пневмоприводами', img:img('solutions/butterfly-pa.webp') },
  { to:'/solutions/ball-ea', name:'Краны шаровые с Электроприводами', img:img('solutions/ball-ea.webp') },
  { to:'/solutions/ball-pa', name:'Краны шаровые с Пневмоприводами', img:img('solutions/ball-pa.webp') },
  { to:'/solutions/gate-pa', name:'Задвижки клиновые с Пневмоприводами', img:img('solutions/gate-pa.webp') },
  { to:'/solutions/gate-ea', name:'Задвижки клиновые с Электроприводами', img:img('solutions/gate-ea.webp') },
  { to:'/solutions/knife-ea', name:'Задвижки шиберные с Электроприводами', img:img('solutions/knife-ea.webp') },
  { to:'/solutions/knife-pa', name:'Задвижки шиберные с Пневмоприводами', img:img('solutions/knife-pa.webp') },
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
