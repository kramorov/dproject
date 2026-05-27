<!-- shared/components/Breadcrumbs.vue -->
<template>
  <nav class="breadcrumbs" v-if="items.length">
    <ol>
      <li v-for="(item, i) in items" :key="i">
        <a v-if="(item.to || item.url) && i < items.length - 1" :href="item.url || item.to || '#'" @click.prevent="onClick(item)" class="crumb-link">{{ item.name }}</a>
        <span v-else>{{ item.name }}</span>
      </li>
    </ol>
  </nav>
</template>
<script setup>
import { useRouter } from 'vue-router'
const props = defineProps({ items: { type: Array, default: () => [] } })
const emit = defineEmits(['navigate'])
const router = useRouter()
function onClick(item) {
  console.log('[Breadcrumbs] onClick', JSON.stringify(item))
  if (item.to) { router.push(item.to); return }
  if (item.url && item.url !== '#') { router.push(item.url); return }
  emit('navigate', item) }
</script>
<style scoped>
.breadcrumbs { margin-bottom: 12px }
.breadcrumbs ol { display:flex; flex-wrap:wrap; list-style:none; padding:0; margin:0; gap:var(--cat-gap-xs); font-size:var(--cat-text-sm); color:var(--cat-muted) }
.breadcrumbs li { display:flex; align-items:center }
.breadcrumbs li::after { content:'/'; margin:0 4px; color:var(--cat-border) }
.breadcrumbs li:last-child::after { content:'' }
.crumb-link { color:var(--cat-primary); text-decoration:none; cursor:pointer }
.crumb-link:hover { text-decoration:underline }
</style>