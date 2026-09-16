<!-- components/header/GlobalSearch.vue -->
<!-- Глобальный поиск модели по артикулу (SKU.code) — отображается в шапке на всех страницах. -->
<template>
  <div class="global-search" ref="root">
    <label class="gs-label" for="gs-article">Глобальный поиск модели по артикулу</label>
    <div class="gs-control">
      <input
        id="gs-article"
        v-model="query"
        class="gs-input"
        type="text"
        autocomplete="off"
        placeholder="Введите артикул…"
        @input="onInput"
        @focus="onFocus"
        @keydown.down.prevent="move(1)"
        @keydown.up.prevent="move(-1)"
        @keydown.enter.prevent="selectCurrent"
        @keydown.esc.prevent="close"
      />
      <div v-if="open && results.length" class="gs-dropdown">
        <button
          v-for="(r, i) in results"
          :key="r.sku_id"
          type="button"
          class="gs-item"
          :class="{ 'gs-item--active': i === activeIndex }"
          @mousedown.prevent="select(r)"
          @mouseenter="activeIndex = i"
        >
          <span class="gs-item__code">{{ r.code }}</span>
          <span class="gs-item__name">{{ r.name }}</span>
          <span class="gs-item__type">{{ r.equipment_type_name }}</span>
        </button>
      </div>
      <div v-else-if="open && query.trim() && !loading" class="gs-dropdown gs-empty">
        Ничего не найдено
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/shared/api'

const router = useRouter()
const root = ref(null)

const query = ref('')
const results = ref([])
const open = ref(false)
const loading = ref(false)
const activeIndex = ref(-1)

let debounceTimer = null
let requestSeq = 0

function onInput() {
  activeIndex.value = -1
  clearTimeout(debounceTimer)
  const q = query.value.trim()
  if (!q) {
    results.value = []
    open.value = false
    loading.value = false
    return
  }
  debounceTimer = setTimeout(() => search(q), 300)
}

async function search(q) {
  const seq = ++requestSeq
  loading.value = true
  try {
    const res = await api.get('/admin/sku/search/', { params: { q } })
    if (seq !== requestSeq) return // устаревший ответ
    results.value = res.data?.results || []
    open.value = true
  } catch (e) {
    if (seq !== requestSeq) return
    results.value = []
    open.value = false
  } finally {
    if (seq === requestSeq) loading.value = false
  }
}

function onFocus() {
  if (query.value.trim() && results.value.length) open.value = true
}

function move(dir) {
  if (!results.value.length) return
  activeIndex.value = (activeIndex.value + dir + results.value.length) % results.value.length
}

function selectCurrent() {
  if (activeIndex.value >= 0 && results.value[activeIndex.value]) {
    select(results.value[activeIndex.value])
  }
}

function select(r) {
  if (!r || r.sku_id == null) return
  close()
  query.value = ''
  results.value = []
  router.push(`/sku/${r.sku_id}`)
}

function close() {
  open.value = false
  activeIndex.value = -1
}

function onClickOutside(e) {
  if (root.value && !root.value.contains(e.target)) close()
}

onMounted(() => document.addEventListener('click', onClickOutside))
onUnmounted(() => {
  document.removeEventListener('click', onClickOutside)
  clearTimeout(debounceTimer)
})
</script>

<style scoped>
.global-search { display: flex; flex-direction: column; justify-content: center; }
.gs-label { font-size: 10px; line-height: 1.2; color: rgba(255, 255, 255, .85); margin-bottom: 2px; white-space: nowrap; }
.gs-control { position: relative; }
.gs-input { width: 280px; height: 28px; padding: 0 12px; font-size: 13px; color: #1f2937; background: #fff; border: 1px solid rgba(255, 255, 255, .4); border-radius: 6px; outline: none; }
.gs-input::placeholder { color: #9ca3af; }
.gs-input:focus { border-color: #fff; box-shadow: 0 0 0 2px rgba(255, 255, 255, .35); }

.gs-dropdown { position: absolute; top: calc(100% + 4px); left: 0; right: 0; background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; box-shadow: 0 8px 30px rgba(0, 0, 0, .15); z-index: 300; overflow: hidden; }
.gs-item { display: flex; flex-direction: column; align-items: flex-start; gap: 1px; width: 100%; padding: 7px 12px; background: none; border: none; cursor: pointer; text-align: left; }
.gs-item:hover, .gs-item--active { background: #f3f6ff; }
.gs-item__code { font-size: 13px; font-weight: 600; color: #1f2937; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%; }
.gs-item__name { font-size: 11px; color: #6b7280; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%; }
.gs-item__type { font-size: 10px; color: var(--cat-primary, #2563eb); }
.gs-empty { padding: 10px 12px; font-size: 12px; color: #9ca3af; }
</style>
