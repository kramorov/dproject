<!-- shared/components/FileViewerModal.vue -->
<!-- Модалка просмотра файла: встроенный показ + развернуть + скачать. -->
<template>
  <div v-if="file" class="fv-overlay" @click.self="$emit('close')">
    <div class="fv-window" :class="{ expanded }">
      <div class="fv-header">
        <h3>{{ file.title || file.file_name || 'Файл' }}</h3>
        <div class="fv-header-actions">
          <button class="fv-icon-btn" @click="expanded = !expanded" :title="expanded ? 'Свернуть' : 'На весь экран'">
            {{ expanded ? '🗗' : '🗖' }}
          </button>
          <a class="fv-icon-btn" :href="file.url" :download="file.file_name" title="Скачать">📥</a>
          <button class="fv-icon-btn" @click="$emit('close')" title="Закрыть">&times;</button>
        </div>
      </div>
      <div class="fv-body">
        <p class="fv-filename" v-if="file.file_name">{{ file.file_name }}</p>
        <iframe
          v-if="file.url"
          class="fv-preview"
          :src="file.url"
          frameborder="0"
        ></iframe>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({ file: { type: Object, default: null } })
defineEmits(['close'])

const expanded = ref(false)
</script>

<style scoped>
.fv-overlay {
  position: fixed; inset: 0; background: var(--cat-overlay);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.fv-window {
  background: var(--cat-surface); border-radius: var(--cat-radius-lg);
  width: 90%; max-width: 860px; max-height: 90vh;
  display: flex; flex-direction: column;
  box-shadow: var(--cat-shadow-modal);
  transition: all .2s;
}
.fv-window.expanded {
  max-width: none; width: 100vw; height: 100vh; max-height: none; border-radius: 0;
}
.fv-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 20px; border-bottom: 1px solid var(--cat-border); flex-shrink: 0;
}
.fv-header h3 { margin: 0; font-size: var(--cat-text-lg); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fv-header-actions { display: flex; align-items: center; gap: var(--cat-gap-xs); flex-shrink: 0; }
.fv-icon-btn {
  text-decoration: none; font-size: 20px; padding: 4px 8px; border-radius: var(--cat-radius-sm);
  transition: background .15s; cursor: pointer; color: var(--cat-muted); background: none; border: none; line-height: 1;
}
.fv-icon-btn:hover { background: var(--cat-border-focus); }
.fv-body { flex: 1; overflow: hidden; display: flex; flex-direction: column; padding: 0; }
.fv-filename { font-size: var(--cat-text-sm); color: var(--cat-muted); margin: 0; padding: 12px 20px 0; flex-shrink: 0; }
.fv-preview { flex: 1; width: 100%; border: none; min-height: 500px; }
</style>