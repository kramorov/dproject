<!-- shared/components/TabSpecs.vue -->
<!-- Рендерит характеристики из sections[type=specs] (data = {группа: {подпись: значение}}) -->
<template>
  <div class="tab-specs" v-if="hasData">
    <div v-for="(fields, groupTitle) in data" :key="groupTitle" class="spec-group">
      <h3 class="group-title">{{ groupTitle }}</h3>
      <dl class="spec-table">
        <div v-for="(value, label) in fields" :key="label" class="spec-row">
          <template v-if="isHtmlBlock(value)">
            <div class="spec-html" v-html="value.__html"></div>
          </template>
          <template v-else>
            <dt>{{ label }}</dt>
            <dd>{{ value || '—' }}</dd>
          </template>
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
  data: { type: Object, default: () => ({}) },
})

const hasData = computed(() => Object.keys(props.data).length > 0)

function isHtmlBlock(value) {
  return !!value && typeof value === 'object' && typeof value.__html === 'string'
}
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
.spec-html { flex: 1; min-width: 0; }
.tab-specs.empty { color: var(--cat-muted-light); font-size: var(--cat-text-base); }
@media (max-width: 768px) { .spec-row dt { width: 140px; } }
</style>
