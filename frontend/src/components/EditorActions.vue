<template>
  <div class="editor-actions" :class="{ 'align-start': align === 'start' }">
    <button v-for="b in buttons" :key="b.key" class="ea-btn"
            :class="`ea-${b.kind || 'default'}`"
            :disabled="b.disabled" @click="$emit('action', b)">
      {{ b.label }}
    </button>
  </div>
</template>

<script setup>
/**
 * Универсальный блок кнопок действий — единый компонент для всех редакторов.
 *
 * Пропсы:
 * - buttons: [{ key, label, kind?: 'primary'|'default'|'danger', disabled? }]
 *   label — уже локализованная строка (t('key') из shared/i18n).
 * - align: 'end' (по умолчанию, прижимается к правому краю) или 'start'.
 *
 * Событие: action(button) — родитель различает кнопки по b.key.
 */
defineProps({
  buttons: { type: Array, default: () => [] },
  align: { type: String, default: 'end' },
})
defineEmits(['action'])
</script>

<style scoped>
.editor-actions { display: flex; gap: 8px; margin-left: auto; }
.editor-actions.align-start { margin-left: 0; }
.ea-btn {
  padding: 6px 14px; cursor: pointer; border-radius: 4px; font-size: 13px;
  border: 1px solid #ccc; background: #fff;
}
.ea-btn.ea-primary { background: #2c6fb0; color: #fff; border-color: #2c6fb0; }
.ea-btn.ea-primary:disabled { background: #9db8d4; border-color: #9db8d4; cursor: not-allowed; }
.ea-btn.ea-danger { background: #c62828; color: #fff; border-color: #c62828; }
</style>
