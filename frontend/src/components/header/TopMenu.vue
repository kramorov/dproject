<template>
  <div class="top-menu">
    <div class="menu-item" v-for="item in visibleItems" :key="item.key" @mouseenter="open=item.key" @mouseleave="open=null; subOpen=null">
      <span class="menu-link has-sub">{{ item.label }} ▾</span>
      <div v-if="item.children && open===item.key" class="dropdown">
        <template v-for="ch in item.children" :key="ch.label">
          <!-- group with sub-dropdown -->
          <div v-if="ch.children" class="dropdown-group" @mouseenter="subOpen=ch.label" @mouseleave="subOpen=null">
            <span class="dropdown-item has-sub">{{ ch.label }} ▸</span>
            <div v-if="subOpen===ch.label" class="sub-dropdown">
              <router-link v-for="sub in ch.children" :key="sub.to" :to="sub.to" class="dropdown-item">{{ sub.label }}</router-link>
            </div>
          </div>
          <!-- regular link -->
          <router-link v-else :to="ch.to" class="dropdown-item">
            {{ ch.label }}
          </router-link>
        </template>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed } from 'vue'
import { useAuth } from './useAuth.js'
const { roles, loaded } = useAuth()
const open = ref(null)
const subOpen = ref(null)

const allItems = [
  { key:'catalog', label:'Каталоги', children:[
    { to:'/catalogs/equipment', label:'Каталоги оборудования' },
    { to:'/catalogs/valves', label:'Каталоги арматуры' },
    { to:'/catalogs/solutions', label:'Каталог готовых решений' },
  ]},
  { key:'configurator', label:'Конфигураторы', children:[
    { to:'/selector/pa', label:'Подбор пневмопривода по моменту' },
    { to:'/configurator/pa', label:'Конфигуратор Пневмоприводов' },
    // { to:'/configurator/pa-legacy', label:'Конфигуратор ПП Old' },
    { to:'/admin/ea-constructor', label:'Конфигуратор Электроприводов' },
    { to:'/configurator/cabinets', label:'Конфигуратор Шкафов управления ЭП' },
    { to:'/configurator/ea-reducers', label:'Конфигуратор Редукторов к ЭП' },
    { to:'/configurator/ea-assemblies', label:'Конфигуратор Сборок арматуры с ЭП' },
    { to:'/configurator/pa-assemblies', label:'Конфигуратор Сборок арматуры с ПП' },
  ]},
  { key:'ai', label:'AI', children:[
    { to:'/ai-debug', label:'AI Отладка' },
  ]},
  { key:'requests', label:'Заявки клиентов', children:[
    { to:'/requests/list', label:'Список заявок' },
    { to:'/admin/customers', label:'Клиенты' },
    { to:'/requests/contractors', label:'Контрагенты' },
  ]},
  { key:'about', label:'О проекте', children:[
    { to:'/about', label:'О проекте' },
    { to:'/about/capabilities', label:'Возможности системы' },
    { to:'/about/benefits-users', label:'Преимущества для пользователей' },
    { to:'/about/benefits-types', label:'Преимущества по типам' },
    { to:'/about/architecture', label:'Архитектура системы' },
    { to:'/about/contacts', label:'Контакты' },
  ]},
  { key:'admin', label:'Администрирование', adminOnly:true, children:[
    { label:'Номенклатура и цены', children:[
      { to:'/admin/price', label:'Цены' },
      { to:'/admin/sku', label:'SKU' },
      { to:'/admin/cert-docs', label:'Сертификаты' },
    ]},
    { label:'Клиенты', children:[
      { to:'/admin/customers', label:'Клиенты' },
    ]},
    { label:'Оборудование', children:[
      { to:'/admin/limit-switch', label:'БКВ' },
      { to:'/admin/ea-power-supply', label:'Опции напряжения ЭП' },
      { to:'/admin/ea-switches', label:'Опции выключателей ЭП' },
      { to:'/admin/ea-models', label:'Модели ЭП' },
      { to:'/admin/ea-wirings', label:'Схемы БУ' },
    ]},
    { label:'Настройка системы', children:[
      { to:'/admin/wizard-config', label:'Мастер подбора' },
      { to:'/admin/media', label:'Медиабиблиотека' },
      { to:'/admin/configurator-rules', label:'Правила конфигуратора' },
      { to:'/admin/permissions', label:'Права доступа' },
    ]},
    { label:'Инструменты', children:[
      { to:'/tools/image-processor', label:'Обработка изображений' },
      { to:'/tools/svg-converter', label:'SVG Конвертер' },
      { to:'/widgets', label:'Виджеты' },
    ]},
    { label:'AI', children:[
      { to:'/ai-assistant', label:'AI Ассистент' },
      { to:'/ai-debug', label:'AI Отладка' },
      { to:'/admin/pipeline-config', label:'Настройка AI Pipeline' },
      { to:'/admin/skill-config', label:'Skill настройка' },
    ]},
  ]},
]

const visibleItems = computed(() => {
  if (!loaded.value) return []
  const isAdmin = roles.value.some(r => r === 'admin' || r === 'system_admin')
  return allItems.filter(item => {
    if (item.adminOnly) return isAdmin
    return true
  })
})
</script>
<style scoped>
.top-menu{display:flex;gap:0;height:100%}
.menu-item{position:relative;display:flex;align-items:center}
.menu-link{padding:8px 14px;font-size:13px;color:var(--site-header-text,#fff);text-decoration:none;border-radius:4px;transition:background .15s;cursor:pointer;white-space:nowrap}
.menu-link:hover,.menu-link.router-link-active{background:rgba(255,255,255,.15)}
.menu-link.has-sub{cursor:default}
.dropdown{position:absolute;top:100%;left:0;min-width:280px;background:var(--cat-surface,#fff);border:1px solid var(--cat-border,#e5e7eb);border-radius:6px;box-shadow:0 4px 20px rgba(0,0,0,.1);z-index:100;padding:4px 0;overflow:visible}
.dropdown-item{display:flex;align-items:center;justify-content:space-between;padding:8px 16px;font-size:13px;color:#1f2937;text-decoration:none;transition:background .1s;white-space:nowrap}
.dropdown-item:hover{background:#f9fafb}
.dropdown-item.has-sub{cursor:default}
.dropdown-group{position:relative}
.sub-dropdown{position:absolute;left:100%;top:0;min-width:240px;background:var(--cat-surface,#fff);border:1px solid var(--cat-border,#e5e7eb);border-radius:6px;box-shadow:0 4px 20px rgba(0,0,0,.1);z-index:101;padding:4px 0}
</style>
