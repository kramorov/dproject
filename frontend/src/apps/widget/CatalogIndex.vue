<!-- widget/CatalogIndex.vue — Стартовая страница: сетка доступных каталогов. -->
<template>
  <div class="catalog-index">
    <h1 class="ci-title">Каталог оборудования</h1>
    <p class="ci-subtitle">Выберите раздел</p>

    <div class="ci-grid">
      <div
        v-for="cat in catalogList"
        :key="cat.id"
        class="ci-card"
        @click="$emit('select', cat.id)"
      >
        <span class="ci-icon">{{ cat.icon }}</span>
        <h3>{{ cat.name }}</h3>
        <p class="ci-desc" v-if="cat.description">{{ cat.description }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  catalogs: { type: Array, default: () => ['gearbox'] },
})

defineEmits(['select'])

const CATALOG_INFO = {
  gearbox:     { id: 'gearbox',     name: 'Редукторы',         icon: '⚙️', description: 'Червячные, цилиндрические, конические' },
  filter_regulator: { id: 'filter_regulator', name: 'Фильтр-регуляторы', icon: '🔧', description: 'Фильтры-регуляторы сжатого воздуха' },
  pneumatic:   { id: 'pneumatic',   name: 'Пневмоприводы',     icon: '💨', description: 'Поршневые, мембранные, SR/SD' },
  electric:    { id: 'electric',    name: 'Электроприводы',    icon: '⚡', description: 'Многооборотные, неполнооборотные' },
  fittings:    { id: 'fittings',    name: 'Пневмофитинги',     icon: '🔧', description: 'Фитинги, трубки, клапаны' },
}

const catalogList = computed(() =>
  props.catalogs.map(id => CATALOG_INFO[id] || { id, name: id, icon: '📦' })
)
</script>

<style scoped>
.catalog-index { }
.ci-title { font-size: var(--cat-text-4xl); font-weight: 700; margin: 0 0 4px; }
.ci-subtitle { font-size: var(--cat-text-md); color: var(--cat-muted); margin: 0 0 var(--cat-gap-3xl); }
.ci-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: var(--cat-gap-2xl); }
.ci-card {
  background: var(--cat-surface);
  border: 1px solid var(--cat-border);
  border-radius: var(--cat-radius-2xl);
  padding: var(--cat-gap-2xl);
  cursor: pointer;
  transition: box-shadow .15s, border-color .15s;
}
.ci-card:hover { box-shadow: var(--cat-shadow-card); border-color: var(--cat-primary); }
.ci-icon { font-size: 40px; display: block; margin-bottom: var(--cat-gap-lg); }
.ci-card h3 { font-size: var(--cat-text-xl); font-weight: 600; margin: 0 0 var(--cat-gap-xs); }
.ci-desc { font-size: var(--cat-text-sm); color: var(--cat-muted); margin: 0; }
</style>
