<template>
  <div class="top-menu">
    <div class="menu-item" v-for="item in visibleItems" :key="item.key" @mouseenter="open=item.key" @mouseleave="open=null">
      <span class="menu-link has-sub">{{ item.label }} ▾</span>
      <div v-if="item.children && open===item.key" class="dropdown">
        <template v-for="ch in item.children" :key="ch.to||ch.label">
          <div v-if="ch.header" class="dropdown-header">{{ ch.header }}</div>
          <router-link v-else :to="ch.to" class="dropdown-item">
            {{ ch.label }}
            <span v-if="ch.pro" class="pro-badge">проф</span>
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

const allItems = [
  { key:'catalog', label:'Каталоги оборудования', children:[
    { to:'/catalog/pneumatic-fittings', label:'Пневмофитинги' },
    { to:'/catalog/filter-regulator', label:'Фильтр-регуляторы' },
    { to:'/catalog/cable-glands', label:'Кабельные вводы' },
    { to:'/catalog/pa-actuators', label:'Пневмоприводы' },
    { to:'/catalog/gearbox', label:'Ручные дублёры' },
    { to:'/catalog/ea-reducers', label:'Редукторы к ЭП', pro:true },
    { to:'/catalog/solenoid-valves', label:'Соленоидные клапаны' },
    { to:'/catalog/positioners', label:'Электропневматические позиционеры' },
    { to:'/catalog/limit-switch', label:'БКВ' },
    { to:'/catalog/ea-actuators', label:'Электроприводы' },
    { to:'/catalog/ea-cabinets', label:'Шкафы управления ЭП', pro:true },
    { to:'/catalog/mounting-kits', label:'Монтажные комплекты и адаптации', pro:true },
  ]},
  { key:'valves', label:'Арматура', children:[
    { to:'/catalog/butterfly-valves', label:'Дисковые затворы' },
    { to:'/catalog/ball-valves', label:'Шаровые краны' },
    { to:'/catalog/gate-valves', label:'Клиновые задвижки' },
    { to:'/catalog/knife-gate-valves', label:'Шиберные задвижки' },
  ]},
  { key:'solutions', label:'Готовые решения', children:[
    { to:'/solutions/butterfly-pa', label:'Сборки Затворов дисковых с Пневмоприводами' },
    { to:'/solutions/ball-pa', label:'Сборки Кранов шаровых с Пневмоприводами' },
    { to:'/solutions/gate-pa', label:'Сборки Клиновых задвижек с Пневмоприводами' },
    { to:'/solutions/knife-pa', label:'Сборки Шиберных задвижек с Пневмоприводами' },
    { to:'/solutions/butterfly-ea', label:'Сборки Затворов дисковых с Электроприводами' },
    { to:'/solutions/ball-ea', label:'Сборки Кранов шаровых с Электроприводами' },
    { to:'/solutions/gate-ea', label:'Сборки Клиновых задвижек с Электроприводами' },
    { to:'/solutions/knife-ea', label:'Сборки Шиберных задвижек с Электроприводами' },
  ]},
  { key:'configurator', label:'Конфигураторы', pro:true, children:[
    { to:'/selector/pa', label:'Подбор пневмопривода по моменту' },
    { to:'/admin/pa-constructor', label:'Конфигуратор Пневмоприводов' },
    { to:'/admin/pa-constructor-legacy', label:'Конфигуратор ПП Old' },
    { to:'/admin/ea-constructor', label:'Конфигуратор Электроприводов' },
    { to:'/configurator/cabinets', label:'Конфигуратор Шкафов управления ЭП' },
    { to:'/configurator/ea-reducers', label:'Конфигуратор Редукторов к ЭП' },
    { to:'/configurator/ea-assemblies', label:'Конфигуратор Сборок арматуры с ЭП' },
    { to:'/configurator/pa-assemblies', label:'Конфигуратор Сборок арматуры с ПП' },
  ]},
  { key:'requests', label:'Заявки клиентов', pro:true, children:[
    { to:'/requests/list', label:'Список заявок' },
    { to:'/admin/customers', label:'Клиенты' },
    { to:'/requests/contractors', label:'Контрагенты' },
  ]},
  { key:'about', label:'О проекте', children:[
    { to:'/about/contacts', label:'Контакты' },
  ]},
  { key:'admin', label:'Администрирование', adminOnly:true, children:[
    { header:'Управление' },
    { to:'/admin/customers', label:'Клиенты' },
    { to:'/admin/media', label:'Медиабиблиотека' },
    { to:'/admin/price', label:'Цены' },
    { to:'/admin/sku', label:'SKU' },
    { to:'/admin/cert-docs', label:'Сертификаты' },
    { header:'Оборудование' },
    { to:'/admin/limit-switch', label:'БКВ' },
    { to:'/admin/ea-power-supply', label:'Опции напряжения ЭП' },
    { to:'/admin/ea-switches', label:'Опции выключателей ЭП' },
    { to:'/admin/ea-models', label:'Модели ЭП' },
    { to:'/admin/ea-wirings', label:'Схемы БУ' },
    { header:'Инструменты' },
    { to:'/tools/image-processor', label:'Обработка изображений' },
    { to:'/tools/svg-converter', label:'SVG Конвертер' },
    { to:'/widgets', label:'Виджеты' },
    { header:'AI' },
    { to:'/ai-assistant', label:'AI Ассистент' },
    { to:'/ai-debug', label:'AI Отладка' },
    { to:'/admin/pipeline-config', label:'Настройка AI Pipeline' },
    { header:'BOM' },
    { to:'/admin/bom-config', label:'BOM Конструктор' },
  ]},
]

const visibleItems = computed(() => {
  if (!loaded.value) return []
  const isAdmin = roles.value.some(r => r === 'admin' || r === 'system_admin')
  const isAuth = roles.value.length > 0 && !isAdmin
  return allItems.filter(item => {
    if (item.adminOnly) return isAdmin
    if (item.pro) return isAuth || isAdmin
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
.dropdown{position:absolute;top:100%;left:0;min-width:280px;background:var(--cat-surface,#fff);border:1px solid var(--cat-border,#e5e7eb);border-radius:6px;box-shadow:0 4px 20px rgba(0,0,0,.1);z-index:100;padding:4px 0;max-height:70vh;overflow-y:auto}
.dropdown-header{font-size:11px;font-weight:600;color:#9ca3af;text-transform:uppercase;padding:8px 16px 4px;letter-spacing:.5px}
.dropdown-item{display:flex;align-items:center;justify-content:space-between;padding:8px 16px;font-size:13px;color:#1f2937;text-decoration:none;transition:background .1s}
.dropdown-item:hover{background:#f9fafb}
.pro-badge{font-size:10px;background:#fef3c7;color:#92400e;padding:1px 6px;border-radius:3px;margin-left:8px;font-weight:500}
</style>
