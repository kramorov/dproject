<!-- shared/components/JsonLd.vue -->
<!-- Schema.org JSON-LD. Внедряется в <head> через DOM API (Vue не разрешает <script> в шаблоне). -->
<template>
  <div style="display:none" data-jsonld />
</template>

<script setup>
import { watch, onMounted, onUnmounted, toRef } from 'vue'

const props = defineProps({
  data: { type: Object, default: null },
})

function injectJsonLd(data) {
  // Удаляем старый
  const old = document.head.querySelector('script[data-jsonld]')
  if (old) old.remove()

  if (!data || !Object.keys(data).length) return

  const script = document.createElement('script')
  script.type = 'application/ld+json'
  script.setAttribute('data-jsonld', '')
  script.textContent = JSON.stringify(data, null, 2)
  document.head.appendChild(script)
}

const dataRef = toRef(props, 'data')

onMounted(() => {
  if (props.data) injectJsonLd(props.data)
})

watch(dataRef, (val) => injectJsonLd(val))

onUnmounted(() => {
  const old = document.head.querySelector('script[data-jsonld]')
  if (old) old.remove()
})
</script>
