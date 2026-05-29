<!-- shared/components/PageTitle.vue — заголовок страницы с контекстом -->
<template>
  <div class="page-title-bar">
    <h1 class="pt-heading">{{ title }}</h1>
    <p class="pt-sub" v-if="subtitle">{{ subtitle }}</p>
    <p class="pt-context" v-if="context">
      <span class="pt-label">{{ contextLabel }}</span>
      <span class="pt-value">{{ context }}</span>
    </p>
  </div>
</template>
<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  context: { type: String, default: '' },
  contextLabel: { type: String, default: '' },
})
</script>
<style scoped>
.page-title-bar {
  margin-bottom: var(--cat-gap-2xl, 24px);
}
.pt-heading {
  font-size: var(--cat-page-title-size, var(--cat-text-4xl, 28px));
  font-weight: var(--cat-page-title-weight, 700);
  color: var(--cat-page-title-color, var(--cat-text, #1f2937));
  margin: 0 0 4px;
  line-height: 1.2;
}
.pt-sub {
  font-size: var(--cat-text-md, 15px);
  color: var(--cat-muted, #6b7280);
  margin: 0 0 8px;
}
.pt-context {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: 4px 0 0;
  padding: 6px 14px;
  background: var(--cat-primary-light, #eff6ff);
  border-radius: var(--cat-radius-md, 8px);
  font-size: var(--cat-text-sm, 13px);
}
.pt-label {
  color: var(--cat-muted, #6b7280);
}
.pt-value {
  color: var(--cat-primary, #2563eb);
  font-weight: 600;
}
</style>
