<!-- shared/components/Breadcrumbs.vue -->
<template>
  <nav class="breadcrumbs" aria-label="Breadcrumb" v-if="items.length">
    <ol>
      <li v-for="(item, i) in items" :key="i">
        <a v-if="item.url && i < items.length - 1" :href="item.url">{{ item.name }}</a>
        <span v-else>{{ item.name }}</span>
      </li>
    </ol>
  </nav>
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] },
})
</script>

<style scoped>
.breadcrumbs { margin-bottom: 12px; }
.breadcrumbs ol {
  display: flex;
  flex-wrap: wrap;
  list-style: none;
  padding: 0;
  margin: 0;
  gap: var(--cat-gap-xs);
  font-size: var(--cat-text-sm);
  color: var(--cat-muted);
}
.breadcrumbs li { display: flex; align-items: center; }
.breadcrumbs li::after { content: '/'; margin: 0 4px; color: var(--cat-border); }
.breadcrumbs li:last-child::after { content: ''; }
.breadcrumbs a { color: var(--cat-primary); text-decoration: none; }
.breadcrumbs a:hover { text-decoration: underline; }
</style>