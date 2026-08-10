<!-- shared/components/EmptyState.vue — Красивое пустое состояние для корзины/избранного -->
<template>
  <div class="es">
    <div class="es-icon">
      <img v-if="type === 'favorites'" src="/favorites-empty.svg" alt="" width="180" height="180" />
      <svg v-else viewBox="0 0 120 120" width="120" height="120" fill="none">
        <circle cx="45" cy="85" r="6" stroke="#d1d5db" stroke-width="2.5" fill="#f9fafb"/>
        <circle cx="85" cy="85" r="6" stroke="#d1d5db" stroke-width="2.5" fill="#f9fafb"/>
        <path d="M15 35h90l-8 50H23l-8-50z" stroke="#d1d5db" stroke-width="2.5" fill="#f9fafb"/>
        <line x1="35" y1="35" x2="45" y2="15" stroke="#d1d5db" stroke-width="2.5" stroke-linecap="round"/>
        <line x1="85" y1="35" x2="75" y2="15" stroke="#d1d5db" stroke-width="2.5" stroke-linecap="round"/>
      </svg>
    </div>
    <h2 class="es-title">{{ title }}</h2>
    <p class="es-text" v-if="text">{{ text }}</p>
    <p class="es-sub" v-if="sub">{{ sub }}</p>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  type: { type: String, default: 'cart' },  // 'cart' | 'favorites'
  title: { type: String, default: '' },
  text: { type: String, default: '' },
  sub: { type: String, default: '' },
})
</script>

<style scoped>
.es { text-align: center; padding: 80px 20px 60px; max-width: 480px; margin: 0 auto; }
.es-icon { margin-bottom: 24px; }
.es-title { font-size: 22px; font-weight: 700; color: var(--cat-text, #1f2937); margin: 0 0 12px; }
.es-text { font-size: 15px; color: var(--cat-muted, #6b7280); line-height: 1.5; margin: 0 0 8px; }
.es-sub { font-size: 13px; color: var(--cat-muted-light, #9ca3af); line-height: 1.4; margin: 0; }
</style>
