<!-- pages/about/AboutSection.vue — страница раздела «О проекте» со слайдером -->
<template>
  <div class="about-section-page">
    <span class="debug-tag">AboutSection</span>

    <Breadcrumbs :items="breadcrumbs" @navigate="onBreadcrumb" />
    <!-- Title moved to AboutSlider top bar -->

    <AboutSlider
      :markdown="markdown"
      :sectionTitle="sectionMeta.title"
      :sectionSubtitle="sectionMeta.subtitle"
      :initialPage="initialPage"
      @update:page="onPageChange"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Breadcrumbs from '@/shared/components/Breadcrumbs.vue'
import AboutSlider from '@/shared/components/AboutSlider.vue'

// Raw markdown imports
import capabilitiesMd from './sections/capabilities.md?raw'
import benefitsUsersMd from './sections/benefits-users.md?raw'
import benefitsTypesMd from './sections/benefits-types.md?raw'
import architectureMd from './sections/architecture.md?raw'

const route = useRoute()
const router = useRouter()

const sectionKey = computed(() => {
  const map = {
    'about-capabilities': 'capabilities',
    'about-benefits-users': 'benefits-users',
    'about-benefits-types': 'benefits-types',
    'about-architecture': 'architecture',
  }
  return map[route.name] || ''
})

const sections = {
  capabilities: {
    title: 'Возможности системы',
    subtitle: 'Каталог, поиск, инженерные инструменты, ИИ-модуль, интеграции и многое другое',
    md: capabilitiesMd,
  },
  'benefits-users': {
    title: 'Преимущества для пользователей системы',
    subtitle: 'Что получает каждый тип участника: производители, инжиниринговые компании, дилеры, партнёры, потребители',
    md: benefitsUsersMd,
  },
  'benefits-types': {
    title: 'Преимущества по типам потребителей',
    subtitle: 'Сводная таблица: какое преимущество даёт система для каждого типа потребителя',
    md: benefitsTypesMd,
  },
  architecture: {
    title: 'Архитектура системы и основные понятия',
    subtitle: 'ИТ-продукты, ролевая модель участников, терминология BOM',
    md: architectureMd,
  },
}

const sectionMeta = computed(() => sections[sectionKey.value] || { title: '', subtitle: '', md: '' })
const markdown = computed(() => sectionMeta.value.md)

const initialPage = computed(() => {
  const p = parseInt(route.query.page)
  return (p > 0) ? p - 1 : 0
})

const breadcrumbs = computed(() => [
  { name: 'Главная', to: '/' },
  { name: 'О проекте', to: '/about' },
  { name: sectionMeta.value.title, to: route.path },
])

function onBreadcrumb(item) {
  if (item.to) router.push(item.to)
}

function onPageChange(pageIdx) {
  // Update query without full navigation, preserving other params
  const newQuery = { ...route.query }
  if (pageIdx === 0) {
    delete newQuery.page
  } else {
    newQuery.page = String(pageIdx + 1)
  }
  router.replace({ query: newQuery })
}
</script>

<style scoped>
.about-section-page {
  max-width: 1000px;
  margin: 0 auto;
}
</style>
