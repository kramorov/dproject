<!-- shared/components/FileList.vue -->
<!-- Список файлов. Клик → открыть в новой вкладке. Кнопка 📥 → скачать сразу. -->
<template>
  <div class="file-list" v-if="files.length">
    <div
      v-for="file in files"
      :key="file.id"
      class="file-row"
    >
      <a
        class="file-item"
        :href="file.url"
        target="_blank"
        rel="noopener"
        :download="null"
      >
        📄 &nbsp;{{ file.title || file.file_name || 'Файл' }}
      </a>
      <a
        class="file-dl-btn"
        :href="file.url"
        :download="file.file_name || true"
        title="Скачать"
      >📥</a>
    </div>
  </div>
  <div class="file-list empty" v-else>
    <span class="no-files">Нет файлов</span>
  </div>
</template>

<script setup>
defineProps({
  files: { type: Array, default: () => [] },
})
</script>

<style scoped>
.file-list { display: flex; flex-direction: column; gap: 6px; }
.file-row {
  display: flex;
  align-items: stretch;
  border: 1px solid var(--cat-border);
  border-radius: var(--cat-radius-md);
  overflow: hidden;
  background: var(--cat-bg);
}
.file-row:hover { border-color: var(--cat-primary); }
.file-item {
  display: flex;
  align-items: center;
  gap: var(--cat-gap-sm);
  flex: 1;
  padding: 8px 12px;
  cursor: pointer;
  font-size: var(--cat-text-base);
  color: var(--cat-text);
  text-align: left;
  background: none;
  border: none;
  outline: none;
  text-decoration: none;
}
.file-item:hover { background: var(--cat-bg-hover); }
.file-dl-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  text-decoration: none;
  font-size: var(--cat-text-lg);
  background: var(--cat-surface);
  border-left: 1px solid var(--cat-border);
  color: var(--cat-muted);
  transition: color .15s, background .15s;
}
.file-dl-btn:hover { color: var(--cat-primary); background: var(--cat-primary-light); }
.no-files { color: var(--cat-muted-light); font-size: var(--cat-text-base); }
</style>
