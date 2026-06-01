<!-- shared/components/DocViewer.vue -->
<!-- Попап для просмотра страниц документа (PDF) с навигацией. -->
<template>
  <Teleport to="body">
    <div v-if="show" class="dv-overlay" @click.self="$emit('close')">
      <div class="dv-window">
        <div class="dv-header">
          <span class="dv-title">{{ title }}</span>
          <span class="dv-counter" v-if="pages.length > 1">{{ current + 1 }} / {{ pages.length }}</span>
          <div class="dv-actions">
            <a :href="downloadUrl" :download="fileName" class="dv-btn">📥</a>
            <button class="dv-close" @click="$emit('close')">✕</button>
          </div>
        </div>
        <div class="dv-body">
          <button v-if="pages.length > 1 && current > 0" class="dv-arrow dv-left" @click="prev">◀</button>
          <img v-if="currentPage" :src="currentPage" class="dv-page" />
          <button v-if="pages.length > 1 && current < pages.length - 1" class="dv-arrow dv-right" @click="next">▶</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import mediaApi from '@/apps/media-library/api'

const props = defineProps({
  show: Boolean,
  fileId: { type: Number, default: null },
  title: { type: String, default: '' },
  fileName: { type: String, default: '' },
  downloadUrl: { type: String, default: '' },
})
defineEmits(['close'])

const pages = ref([])
const current = ref(0)

const currentPage = computed(() => pages.value[current.value] || null)

function prev() { if (current.value > 0) current.value-- }
function next() { if (current.value < pages.value.length - 1) current.value++ }

function onKey(e) {
  if (e.key === 'ArrowLeft') prev()
  if (e.key === 'ArrowRight') next()
  if (e.key === 'Escape') emit('close')
}

watch(() => props.show, async (val) => {
  if (val && props.fileId) {
    pages.value = []
    current.value = 0
    document.addEventListener('keydown', onKey)
    try {
      const { data } = await mediaApi.getVariants(props.fileId)
      if (data.variants?.pages) {
        pages.value = data.variants.pages.map(p => {
          return p.page ? Object.values(p.page)[0] : (p.icon ? Object.values(p.icon)[0] : null)
        }).filter(Boolean)
      }
    } catch {}
  } else {
    document.removeEventListener('keydown', onKey)
  }
})

onUnmounted(() => document.removeEventListener('keydown', onKey))
</script>

<style scoped>
.dv-overlay {
  position: fixed; inset: 0; z-index: 3000; background: rgba(0,0,0,0.92);
  display: flex; align-items: center; justify-content: center;
}
.dv-window { width: 95vw; height: 95vh; display: flex; flex-direction: column; }
.dv-header {
  display: flex; align-items: center; gap: 12px; padding: 10px 16px;
  color: #fff; font-size: 14px; flex-shrink: 0;
}
.dv-title { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dv-counter { color: #9ca3af; font-size: 13px; }
.dv-actions { display: flex; gap: 8px; align-items: center; }
.dv-btn { color: #fff; text-decoration: none; font-size: 18px; padding: 4px 8px; }
.dv-close { background: none; border: none; color: #fff; font-size: 24px; cursor: pointer; }
.dv-body {
  flex: 1; display: flex; align-items: center; justify-content: center;
  position: relative; min-height: 0;
}
.dv-page { max-width: 100%; max-height: 100%; object-fit: contain; }
.dv-arrow {
  position: absolute; top: 50%; transform: translateY(-50%); z-index: 10;
  background: rgba(0,0,0,0.5); border: 2px solid rgba(255,255,255,0.3);
  color: #fff; font-size: 24px; width: 44px; height: 44px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; border-radius: 50%;
}
.dv-arrow:hover { background: rgba(0,0,0,0.8); border-color: #fff; }
.dv-left { left: 4px; }
.dv-right { right: 4px; }
</style>
