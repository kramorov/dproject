<template>
  <Teleport to="body">
    <div v-if="show && currentItem" class="viewer-overlay" @click.self="$emit('close')" @keydown="onKey">
      <!-- Заголовок -->
      <div class="viewer-toolbar">
        <span class="viewer-title">{{ currentItem?.name || 'Просмотр' }}</span>
        <span class="viewer-counter" v-if="items.length > 1">{{ index + 1 }} / {{ items.length }}</span>
        <button class="viewer-close" @click.stop="$emit('close')">&times;</button>
      </div>

      <!-- Стрелки -->
      <button
        v-if="items.length > 1"
        class="viewer-arrow viewer-arrow-left"
        @click.stop="prev"
      >◀</button>
      <button
        v-if="items.length > 1"
        class="viewer-arrow viewer-arrow-right"
        @click.stop="next"
      >▶</button>

      <!-- Контент -->
      <div class="viewer-content">
        <!-- Изображение -->
        <img
            v-if="isImage(currentItem.mime_type)"
            :src="viewUrl(currentItem.id)"
            :alt="currentItem.name"
            class="viewer-img"
          />
          <!-- PDF (встроенный просмотрщик браузера, листание страниц) -->
          <iframe
            v-else-if="currentItem.mime_type === 'application/pdf'"
            :src="downloadUrl(currentItem.id)"
            class="viewer-pdf"
            frameborder="0"
          />
          <!-- Остальные типы — скачать -->
          <div v-else class="viewer-unsupported">
            <p>📁 {{ currentItem.file_name || currentItem.name }}</p>
            <p>Предпросмотр недоступен</p>
            <a :href="downloadUrl(currentItem.id)" target="_blank" class="viewer-dl-link">Скачать</a>
          </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  show: Boolean,
  items: { type: Array, default: () => [] },
  index: { type: Number, default: 0 },
})
const emit = defineEmits(['close', 'update:index'])

const currentItem = computed(() => props.items[props.index] || null)

function viewUrl(id) {
  return `/api/media/${id}/view/`
}
function downloadUrl(id) {
  return `/api/media/${id}/download/`
}

function isImage(mime) {
  return mime && mime.startsWith('image/')
}

function prev() {
  if (props.index > 0) emit('update:index', props.index - 1)
}

function next() {
  if (props.index < props.items.length - 1) emit('update:index', props.index + 1)
}

function onKey(e) {
  if (e.key === 'Escape') emit('close')
  if (e.key === 'ArrowLeft') prev()
  if (e.key === 'ArrowRight') next()
}

onMounted(() => document.addEventListener('keydown', onKey))
onUnmounted(() => document.removeEventListener('keydown', onKey))
</script>

<style scoped>
.viewer-overlay {
  position: fixed; inset: 0; z-index: 2000;
  background: rgba(0,0,0,0.92);
  display: flex; align-items: center; justify-content: center;
}
.viewer-toolbar {
  position: absolute; top: 0; left: 0; right: 0; height: 44px;
  display: flex; align-items: center; gap: 12px;
  padding: 0 16px; background: rgba(0,0,0,0.5);
  color: #fff; font-size: 14px; z-index: 10;
}
.viewer-title { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.viewer-counter { color: #9ca3af; font-size: 13px; }
.viewer-close {
  background: none; border: none; color: #fff; font-size: 28px;
  cursor: pointer; padding: 0 4px; line-height: 1;
}
.viewer-arrow {
  position: absolute; top: 50%; transform: translateY(-50%);
  background: rgba(255,255,255,0.1); border: none; color: #fff;
  font-size: 32px; padding: 12px 16px; cursor: pointer; z-index: 10;
  border-radius: 4px; transition: background 0.15s;
}
.viewer-arrow:hover { background: rgba(255,255,255,0.25); }
.viewer-arrow-left  { left: 12px; }
.viewer-arrow-right { right: 12px; }
.viewer-content {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  padding: 60px;
}
.viewer-img {
  max-width: 100%; max-height: 100%; object-fit: contain;
}
.viewer-pdf {
  width: 80%; height: 90%; border: none; background: #fff;
}
.viewer-unsupported {
  text-align: center; color: #fff; font-size: 16px;
}
.viewer-unsupported p { margin: 8px 0; }
.viewer-dl-link {
  display: inline-block; margin-top: 12px; padding: 8px 20px;
  background: #2563eb; color: #fff; border-radius: 6px; text-decoration: none;
}
</style>
