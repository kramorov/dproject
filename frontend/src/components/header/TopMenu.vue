<template>
  <div class="top-menu">
    <div class="menu-item" v-for="item in visibleItems" :key="item.key" @mouseenter="open=item.key" @mouseleave="open=null; subOpen=null">
      <span class="menu-link has-sub">{{ t(item.label) }} ▾</span>
      <div v-if="item.children && open===item.key" class="dropdown">
        <template v-for="ch in item.children" :key="ch.label">
          <!-- group with sub-dropdown -->
          <div v-if="ch.children" class="dropdown-group" @mouseenter="subOpen=ch.label" @mouseleave="subOpen=null">
            <span class="dropdown-item has-sub">{{ t(ch.label) }} ▸</span>
            <div v-if="subOpen===ch.label" class="sub-dropdown">
              <router-link v-for="sub in ch.children" :key="sub.to" :to="localizedPath(sub.to, locale)" class="dropdown-item">{{ t(sub.label) }}</router-link>
            </div>
          </div>
          <!-- regular link -->
          <router-link v-else :to="localizedPath(ch.to, locale)" class="dropdown-item">
            {{ t(ch.label) }}
          </router-link>
        </template>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed } from 'vue'
import { useAuth } from './useAuth.js'
import { useI18n, localizedPath } from '@/shared/i18n'
const { roles, loaded } = useAuth()
const { locale, t } = useI18n()
const open = ref(null)
const subOpen = ref(null)

const allItems = [
  { key:'catalog', label:'menu.catalogs', children:[
    { to:'/catalogs/equipment', label:'menu.catalogEquipment' },
    { to:'/catalogs/valves', label:'menu.catalogValves' },
    { to:'/catalogs/solutions', label:'menu.catalogSolutions' },
  ]},
  { key:'configurator', label:'menu.configurators', children:[
    { to:'/selector/pa', label:'menu.paTorqueSelector' },
    { to:'/configurator/pa', label:'menu.paConfigurator' },
    { to:'/admin/posi-constructor', label:'menu.posiConfigurator' },
    { to:'/configurator/pa-kit', label:'menu.assemblyConfigurator' },
    // { to:'/configurator/pa-legacy', label:'Конфигуратор ПП Old' },
    { to:'/admin/ea-constructor', label:'menu.eaConfigurator' },
    { to:'/admin/cg-constructor', label:'menu.cgConfigurator' },
    { to:'/configurator/cabinets', label:'menu.cabinetsConfigurator' },
    { to:'/configurator/ea-reducers', label:'menu.eaReducersConfigurator' },
    { to:'/configurator/ea-assemblies', label:'menu.eaAssembliesConfigurator' },
    { to:'/configurator/pa-assemblies', label:'menu.paAssembliesConfigurator' },
  ]},
  { key:'ai', label:'menu.ai', children:[
    { to:'/ai-debug', label:'menu.aiDebug' },
  ]},
  { key:'requests', label:'menu.requests', children:[
    { to:'/requests/list', label:'menu.requestList' },
    { to:'/admin/customers', label:'menu.customers' },
    { to:'/requests/contractors', label:'menu.contractors' },
  ]},
  { key:'about', label:'menu.about', children:[
    { to:'/about', label:'menu.aboutProject' },
    { to:'/about/capabilities', label:'menu.aboutCapabilities' },
    { to:'/about/benefits-users', label:'menu.aboutBenefitsUsers' },
    { to:'/about/benefits-types', label:'menu.aboutBenefitsTypes' },
    { to:'/about/architecture', label:'menu.aboutArchitecture' },
    { to:'/about/contacts', label:'menu.aboutContacts' },
  ]},
  { key:'admin', label:'menu.admin', adminOnly:true, children:[
    { label:'menu.itemsPrices', children:[
      { to:'/admin/price', label:'menu.prices' },
      { to:'/admin/sku', label:'SKU' },
      { to:'/admin/cert-docs', label:'menu.certificates' },
    ]},
    { label:'menu.customers', children:[
      { to:'/admin/customers', label:'menu.customers' },
    ]},
    { label:'menu.equipment', children:[
      { to:'/admin/limit-switch', label:'menu.lsb' },
      { to:'/admin/ea-power-supply', label:'menu.eaPowerSupply' },
      { to:'/admin/ea-switches', label:'menu.eaSwitches' },
      { to:'/admin/ea-models', label:'menu.eaModels' },
      { to:'/admin/ea-wirings', label:'menu.cuSchematics' },
    ]},
    { label:'menu.systemSettings', children:[
      { to:'/admin/wizard-config', label:'menu.wizard' },
      { to:'/admin/media', label:'menu.mediaLibrary' },
      { to:'/admin/configurator-rules', label:'menu.configuratorRules' },
      { to:'/admin/permissions', label:'menu.permissions' },
    ]},
    { label:'menu.tools', children:[
      { to:'/tools/image-processor', label:'menu.imageProcessing' },
      { to:'/tools/svg-converter', label:'menu.svgConverter' },
      { to:'/tools/table-ocr', label:'menu.ocr' },
      { to:'/widgets', label:'menu.widgets' },
    ]},
    { label:'AI', children:[
      { to:'/ai-assistant', label:'menu.aiAssistant' },
      { to:'/ai-debug', label:'menu.aiDebug' },
      { to:'/admin/pipeline-config', label:'menu.aiPipeline' },
      { to:'/admin/skill-config', label:'menu.skillSettings' },
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
