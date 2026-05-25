<!-- shared/components/TabSpecs.vue -->
<!-- Рендерит характеристики из sections[type=specs] с метаданными из стора -->
<template>
  <div class="tab-specs" v-if="groups.length">
    <div v-for="group in sortedGroups" :key="group.key" class="spec-group">
      <h3 class="group-title" v-if="group.title">{{ group.title }}</h3>
      <dl class="spec-table">
        <div v-for="field in group.fields" :key="field.key" class="spec-row">
          <dt>{{ field.label }}{{ field.unit ? ', ' + field.unit : '' }}</dt>
          <dd>{{ field.value || '—' }}</dd>
        </div>
      </dl>
    </div>
  </div>
  <div class="tab-specs empty" v-else>
    Нет характеристик
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  groups: { type: Array, default: () => [] },
})

const sortedGroups = computed(() =>
  [...props.groups].sort((a, b) => (a.order || 99) - (b.order || 99))
)
</script>

<style scoped>
.tab-specs { }
.spec-group { margin-bottom: 20px; }
.group-title {
  font-size: var(--cat-text-md);
  font-weight: 600;
  color: var(--cat-text-soft);
  margin: 0 0 8px;
  padding-bottom: var(--cat-gap-sm);
  border-bottom: 1px solid var(--cat-border);
}
.spec-table { display: grid; gap: 0; }
.spec-row {
  display: flex;
  padding: var(--cat-specs-row-padding);
  border-bottom: var(--cat-specs-border);
}
.spec-row:nth-child(even) { background: var(--cat-specs-stripe-bg); }
.spec-row:last-child { border-bottom: none; }
.spec-row dt {
  width: var(--cat-specs-label-width);
  font-size: var(--cat-text-sm);
  color: var(--cat-muted);
  flex-shrink: 0;
}
.spec-row dd {
  font-size: var(--cat-text-base);
  color: var(--cat-text);
  margin: 0;
}
.tab-specs.empty { color: var(--cat-muted-light); font-size: var(--cat-text-base); }
@media (max-width: 768px) { .spec-row dt { width: 140px; } }
</style>