<!-- shared/components/AboutSlider.vue — слайдер-презентация разделов «О проекте» -->
<template>
  <div class="as-root" ref="sliderRoot" tabindex="0" @keydown="onKeydown">
    <span class="debug-tag">AboutSlider</span>

    <!-- Top bar: "О проекте" + section title + subtitle -->
    <div class="as-topbar">
      <span class="as-topbar-label">О проекте</span>
      <div class="as-topbar-divider"></div>
      <div class="as-topbar-section">
        <span class="as-topbar-title">{{ sectionTitle }}</span>
        <span class="as-topbar-sub" v-if="sectionSubtitle">{{ sectionSubtitle }}</span>
      </div>
    </div>

    <!-- Main layout: left accent + content + right accent -->
    <div class="as-body">
      <div class="as-accent"></div>

      <div class="as-content-area">
        <!-- Page indicator chip -->
        <div class="as-page-chip" v-if="pages.length > 1">
          <span class="as-chip-num">{{ current + 1 }}</span>
          <span class="as-chip-sep">/</span>
          <span class="as-chip-total">{{ pages.length }}</span>
        </div>

        <!-- Slides -->
        <div class="as-slides-track">
          <transition name="as-fade" mode="out-in">
            <div :key="current" class="as-slide">
              <div class="as-slide-content" v-html="currentPage.html"></div>
            </div>
          </transition>
        </div>

        <!-- Dot navigation -->
        <div class="as-dots" v-if="pages.length > 1">
          <button
            v-for="(page, i) in pages"
            :key="i"
            class="as-dot"
            :class="{ active: i === current }"
            @click="goTo(i)"
            :aria-label="'Страница ' + (i + 1)"
            :title="page.title"
          ></button>
        </div>
      </div>

      <div class="as-accent as-accent-right"></div>
    </div>

    <!-- Bottom bar -->
    <div class="as-bottombar">
      <button class="as-nav-arrow" :disabled="current === 0" @click="prev" aria-label="Назад">
        ←
      </button>
      <span class="as-page-label">Страница {{ current + 1 }} из {{ pages.length }}</span>
      <button class="as-nav-arrow" :disabled="current === pages.length - 1" @click="next" aria-label="Вперёд">
        →
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  markdown: { type: String, required: true },
  sectionTitle: { type: String, default: '' },
  sectionSubtitle: { type: String, default: '' },
  prevLabel: { type: String, default: 'Назад' },
  nextLabel: { type: String, default: 'Вперёд' },
  initialPage: { type: Number, default: 0 },
})

const emit = defineEmits(['update:page'])

function parsePages(md) {
  const tokens = marked.lexer(md)
  const raw = []
  let currentTitle = ''
  let currentTokens = []

  for (const token of tokens) {
    if (token.type === 'heading' && token.depth === 3) {
      if (currentTokens.length > 0) {
        raw.push({ title: currentTitle, html: marked.parser(currentTokens) })
      }
      currentTitle = token.text
      currentTokens = [token]
    } else if (token.type === 'heading' && token.depth === 2) {
      continue
    } else {
      currentTokens.push(token)
    }
  }
  if (currentTokens.length > 0) {
    raw.push({ title: currentTitle, html: marked.parser(currentTokens) })
  }
  if (raw.length === 0 && tokens.length > 0) {
    const h2 = tokens.find(t => t.type === 'heading' && t.depth === 2)
    raw.push({ title: h2 ? h2.text : '', html: marked.parser(tokens) })
  }

  // Filter out pages with no visible content
  return raw.filter(p => {
    const stripped = p.html.replace(/<[^>]+>/g, '').replace(/\s+/g, '').trim()
    return stripped.length > 0
  })
}

const pages = computed(() => parsePages(props.markdown))
const current = ref(Math.max(0, props.initialPage))

watch(() => props.markdown, () => { current.value = 0 })

const currentPage = computed(() => pages.value[current.value] || null)

function goTo(idx) {
  if (idx >= 0 && idx < pages.value.length) {
    current.value = idx
    emit('update:page', idx)
  }
}

function prev() { goTo(current.value - 1) }
function next() { goTo(current.value + 1) }

function onKeydown(e) {
  if (e.key === 'ArrowLeft') { e.preventDefault(); prev() }
  if (e.key === 'ArrowRight') { e.preventDefault(); next() }
}

defineExpose({ goTo, current, pageCount: computed(() => pages.value.length) })
</script>

<style scoped>
/* === Root === */
.as-root {
  max-width: 860px;
  margin: 0 auto;
  outline: none;
  font-family: var(--cat-font, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif);
}

/* === Top bar === */
.as-topbar {
  background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
  border-radius: 14px 14px 0 0;
  padding: 14px 24px;
  display: flex;
  align-items: flex-start;
  gap: 18px;
}
.as-topbar-label {
  color: rgba(255,255,255,0.85);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  white-space: nowrap;
  padding-top: 2px;
}
.as-topbar-divider {
  width: 1px;
  background: rgba(255,255,255,0.25);
  align-self: stretch;
  flex-shrink: 0;
}
.as-topbar-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.as-topbar-title {
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  line-height: 1.3;
}
.as-topbar-sub {
  color: rgba(255,255,255,0.7);
  font-size: 12px;
  line-height: 1.4;
}

/* === Body === */
.as-body {
  display: flex;
  background: #fff;
  border-left: 1px solid #e9d5ff;
  border-right: 1px solid #e9d5ff;
}

/* Accent strips */
.as-accent {
  width: 64px;
  flex-shrink: 0;
  background: linear-gradient(180deg, #7c3aed 0%, #a855f7 50%, #7c3aed 100%);
  position: relative;
}
.as-accent::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 6px;
  height: 48px;
  border-radius: 3px;
  background: rgba(255,255,255,0.25);
}

/* Content area */
.as-content-area {
  flex: 1;
  padding: 16px 32px 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 610px;
}

/* Page chip */
.as-page-chip {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  margin-bottom: 12px;
  color: #a855f7;
  font-weight: 600;
  font-size: 13px;
}
.as-chip-num { font-size: 16px; color: #7c3aed; }
.as-chip-sep { opacity: 0.4; }
.as-chip-total { opacity: 0.5; }

/* === Slides === */
.as-slides-track {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}
.as-slide { min-height: 100%; }
.as-slide-content {
  font-size: 15px;
  line-height: 1.75;
  color: #374151;
}

.as-fade-enter-active,
.as-fade-leave-active { transition: opacity 0.3s ease; }
.as-fade-enter-from,
.as-fade-leave-to { opacity: 0; }

/* Markdown */
.as-slide-content :deep(h4) { font-size: 16px; font-weight: 600; color: #1e1b4b; margin: 12px 0 6px; }
.as-slide-content :deep(p) { margin: 0 0 8px; }
.as-slide-content :deep(ul), .as-slide-content :deep(ol) { margin: 0 0 10px; padding-left: 18px; }
.as-slide-content :deep(li) { margin-bottom: 3px; }
.as-slide-content :deep(strong) { color: #1e1b4b; }
.as-slide-content :deep(table) { width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 13px; }
.as-slide-content :deep(th) { background: #f3e8ff; color: #4c1d95; font-weight: 600; text-align: left; padding: 7px 10px; border-bottom: 2px solid #e9d5ff; }
.as-slide-content :deep(td) { padding: 7px 10px; border-bottom: 1px solid #f3e8ff; vertical-align: top; }
.as-slide-content :deep(tr:hover td) { background: #faf5ff; }
.as-slide-content :deep(hr) { border: none; border-top: 1px solid #e9d5ff; margin: 16px 0; }
.as-slide-content :deep(a) { color: #7c3aed; }
.as-slide-content :deep(blockquote) { border-left: 3px solid #a855f7; padding: 6px 12px; margin: 10px 0; background: #faf5ff; border-radius: 0 6px 6px 0; }
.as-slide-content :deep(code) { background: #f3e8ff; padding: 1px 5px; border-radius: 3px; font-size: 13px; color: #4c1d95; }

/* === Dots === */
.as-dots {
  display: flex;
  justify-content: center;
  gap: 7px;
  padding: 14px 0 0;
  margin-top: auto;
}
.as-dot {
  width: 9px; height: 9px;
  border-radius: 50%;
  border: none;
  background: #d8b4fe;
  cursor: pointer;
  transition: all 0.25s;
  padding: 0;
}
.as-dot:hover { background: #a855f7; transform: scale(1.2); }
.as-dot.active { background: #7c3aed; width: 24px; border-radius: 5px; }

/* === Bottom bar === */
.as-bottombar {
  background: linear-gradient(135deg, #7c3aed 0%, #9333ea 100%);
  border-radius: 0 0 14px 14px;
  padding: 10px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.as-nav-arrow {
  width: 32px; height: 32px;
  border-radius: 50%;
  border: 2px solid rgba(255,255,255,0.3);
  background: transparent;
  color: #fff;
  font-size: 15px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.as-nav-arrow:hover:not(:disabled) { background: rgba(255,255,255,0.15); border-color: rgba(255,255,255,0.6); }
.as-nav-arrow:disabled { opacity: 0.3; cursor: not-allowed; }
.as-page-label { color: rgba(255,255,255,0.8); font-size: 12px; font-weight: 500; }
</style>
