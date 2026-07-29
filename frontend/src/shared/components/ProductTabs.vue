<!-- shared/components/ProductTabs.vue -->
<template>
  <div class="product-tabs" v-if="tabs.length">
    <div class="tabs">
      <button v-for="t in tabs" :key="t.key" class="tab-btn" :class="{ active: active === t.key }" @click="active = t.key">{{ t.title }}</button>
    </div>
    <div class="tab-content"><slot :activeTab="active" /></div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
const props = defineProps({ tabs: { type: Array, default: () => [] }, defaultTab: { type: String, default: '' } })
const emit = defineEmits(['update:activeTab'])
const active = ref(props.defaultTab || props.tabs[0]?.key || '')
watch(active, (val) => emit('update:activeTab', val))
  watch(() => props.defaultTab, (val) => { if (val) active.value = val })
  watch(() => props.tabs, (val) => { if (val.length && !active.value) active.value = val[0]?.key || '' })
</script>

<style scoped>
.tabs { display: flex; gap: 0; border-bottom: var(--cat-tab-border-width) solid var(--cat-border); margin-bottom: var(--cat-gap-2xl); }
.tab-btn { padding: var(--cat-tab-padding); font-size: var(--cat-tab-font-size); background: none; border: none; border-bottom: var(--cat-tab-border-width) solid transparent; margin-bottom: calc(-1 * var(--cat-tab-border-width)); cursor: pointer; color: var(--cat-muted); transition: color .15s, border-color .15s; }
.tab-btn:hover { color: var(--cat-text); }
.tab-btn.active { color: var(--cat-primary); border-bottom-color: var(--cat-primary); }
.tab-content { }
</style>
