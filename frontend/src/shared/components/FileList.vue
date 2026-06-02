<!-- shared/components/FileList.vue -->
<!-- Список файлов с превью, оригиналом и сжатой версией. -->
<template>
  <div class="file-list" v-if="files.length">
    <div v-for="file in files" :key="file.id" class="file-row">
      <img v-if="file.preview_url" :src="file.preview_url" class="file-preview" />
      <span v-else class="file-preview file-preview-icon">📄</span>
      <div class="file-info">
        <span class="file-name">{{ file.name || file.file_name || 'Файл' }}</span>
        <div class="file-links">
          <a href="#" @click.prevent="openDoc(file)" class="file-link">👁️ Открыть</a>
          <a :href="file.url" :download="file.file_name || file.name || true" class="file-link">📥 Скачать</a>
          <a v-if="file.email_url" :href="file.email_url"
             :download="file.email_file_name || (file.file_name || file.name || 'file') + ' (сжат).pdf'" class="file-link file-link-email">
            📧 Сжат
          </a>
        </div>
      </div>
    </div>
  </div>
  <div class="file-list empty" v-else>
    <span class="no-files">Нет файлов</span>
  </div>
  <DocViewer
    :show="viewerShow"
    :file-id="viewerFile?.id"
    :title="viewerFile?.name || ''"
    :file-name="viewerFile?.file_name || viewerFile?.name || ''"
    :download-url="viewerFile?.url || ''"
    @close="viewerShow = false"
  />
</template>

<script setup>
import { ref } from 'vue'
import DocViewer from './DocViewer.vue'

defineProps({
  files: { type: Array, default: () => [] },
})

const viewerShow = ref(false)
const viewerFile = ref(null)

function openDoc(file) {
  viewerFile.value = file
  viewerShow.value = true
}
</script>

<style scoped>
.file-list { display: flex; flex-direction: column; gap: 6px; }
.file-row {
  display: flex; align-items: center; gap: 10px;
  border: 1px solid var(--cat-border); border-radius: var(--cat-radius-md);
  padding: 8px 12px; background: var(--cat-bg);
}
.file-row:hover { border-color: var(--cat-primary); }
.file-preview { width: 40px; height: 56px; object-fit: contain; border-radius: 3px; flex-shrink: 0; }
.file-preview-icon { display: flex; align-items: center; justify-content: center; font-size: 24px; background: #f3f4f6; border-radius: 3px; }
.file-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.file-name { font-size: var(--cat-text-base); color: var(--cat-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.file-links { display: flex; gap: 12px; }
.file-link { font-size: 13px; color: var(--cat-primary); text-decoration: none; }
.file-link:hover { text-decoration: underline; }
.file-link-email { color: #059669; }
.no-files { color: var(--cat-muted-light); font-size: var(--cat-text-base); }
</style>
