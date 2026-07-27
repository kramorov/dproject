<template>
  <div v-if="running" class="pb-wrap">
    <div class="pb-fill" :style="{width: percent + '%'}" />
    <span class="pb-text">{{ text }}</span>
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'

const props = defineProps({
  text: { type: String, default: 'Загрузка...' },
  durationSec: { type: Number, default: 5 },
  segments: { type: Number, default: 10 },
  running: { type: Boolean, default: false },
})

const emit = defineEmits(['completed'])

const percent = ref(0)
let timer = null

watch(() => props.running, (val) => {
  if (val) {
    percent.value = 0
    const stepMs = Math.max(props.durationSec * 1000 / props.segments, 200)
    timer = setInterval(() => {
      percent.value = Math.min(percent.value + (100 / props.segments), 95)
    }, stepMs)
  } else {
    if (timer) { clearInterval(timer); timer = null }
    if (percent.value > 0) {
      percent.value = 100
      setTimeout(() => { percent.value = 0; emit('completed') }, 300)
    }
  }
})

onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
.pb-wrap { position: relative; height: 32px; background: #e0e0e0; border-radius: 4px; margin: 8px 0; overflow: hidden; }
.pb-fill { height: 100%; background: linear-gradient(90deg, #1976d2, #42a5f5); transition: width 0.3s; border-radius: 4px; }
.pb-text { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 600; color: #333; }
</style>
