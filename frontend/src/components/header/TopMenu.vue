<template>
  <div class="top-menu">
    <div class="menu-item" v-for="item in visibleItems" :key="item.key" @mouseenter="open=item.key" @mouseleave="open=null">
      <router-link v-if="item.to" :to="item.to" class="menu-link">{{ item.label }}</router-link>
      <span v-else class="menu-link has-sub">{{ item.label }} ▾</span>
      <div v-if="item.children && open===item.key" class="dropdown">
        <router-link v-for="ch in item.children" :key="ch.to" :to="ch.to" class="dropdown-item">{{ ch.label }}</router-link>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed } from 'vue'
import { useAuth } from './useAuth.js'
const { role, loaded } = useAuth()
const open = ref(null)
const allItems = [
  { key:'pneumatic', label:'🔧 Пневмоприводы и управление', children:[
    { to:'/catalog/gearbox', label:'Ручные дублёры' },
    { to:'/catalog/filter-regulator', label:'Фильтр-регуляторы' },
    { to:'/catalog/limit-switch', label:'Блоки концевых выключателей' },
    { to:'/catalog/solenoid-valves', label:'Распределительные клапаны' },
    { to:'/catalog/pneumatic-fittings', label:'Пневматические фитинги' },
  ]},
  { key:'electric', label:'⚡ Электроприводы', children:[
    { to:'/catalog/limit-switch', label:'Блоки концевых выключателей' },
  ]},
  { key:'admin', label:'⚙️ Администрирование', adminOnly:true, children:[
    { to:'/admin/cert-docs', label:'📜 Сертификаты' },
    { to:'/admin/media', label:'🖼️ Медиабиблиотека' },
    { to:'/admin/price', label:'💰 Цены' },
    { to:'/admin/sku', label:'📦 SKU' },
    { to:'/admin/limit-switch', label:'🔌 БКВ' },
    { to:'/admin/pa-constructor', label:'🔧 Конструктор пневмоприводов' },
    { to:'/admin/ea-constructor', label:'⚡ Конструктор электроприводов' },
    { to:'/admin/ea-power-supply', label:'🔌 Опции напряжения ЭП' },
    { to:'/admin/ea-switches', label:'🔘 Опции выключателей ЭП' },
    { to:'/admin/ea-models', label:'📋 Модели ЭП' },
    { to:'/admin/ea-wirings', label:'🔗 Схемы БУ' },
    { to:'/widgets', label:'📋 Виджеты' },
  ]},
]
const visibleItems = computed(() => loaded.value ? allItems.filter(i => !i.adminOnly || role.value === 'admin') : [])
</script>
<style scoped>
.top-menu{display:flex;gap:0;height:100%}
.menu-item{position:relative;display:flex;align-items:center}
.menu-link{padding:8px 14px;font-size:13px;color:var(--site-header-text);text-decoration:none;border-radius:4px;transition:background .15s;cursor:pointer;white-space:nowrap}
.menu-link:hover,.menu-link.router-link-active{background:rgba(255,255,255,.15)}
.menu-link.has-sub{cursor:default}
.dropdown{position:absolute;top:100%;left:0;min-width:240px;background:var(--cat-surface,#fff);border:1px solid var(--cat-border,#e5e7eb);border-radius:var(--cat-radius-md,6px);box-shadow:0 4px 20px rgba(0,0,0,.1);z-index:100;padding:4px 0}
.dropdown-item{display:block;padding:8px 16px;font-size:13px;color:var(--cat-text,#1f2937);text-decoration:none;transition:background .1s}
.dropdown-item:hover{background:var(--cat-bg,#f9fafb)}
</style>