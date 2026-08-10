<!-- shared/components/CartIcon.vue -->
<template>
  <div class="cart-icon" @click="emit('toggle')">
    <span class="cart-icon__emoji">🛒</span>
    <span v-if="count > 0" class="cart-icon__badge">{{ count }}</span>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import cartService from '@/shared/services/cartService'

const emit = defineEmits(['toggle'])
const count = ref(0)

async function updateCount() {
  try {
    const res = await cartService.getActive()
    count.value = res.data?.total_quantity || res.data?.item_count || 0
  } catch {
    count.value = 0
  }
}

function onCartUpdated() { updateCount() }

onMounted(() => {
  updateCount()
  window.addEventListener('cart-updated', onCartUpdated)
})
onUnmounted(() => {
  window.removeEventListener('cart-updated', onCartUpdated)
})
</script>

<style scoped>
.cart-icon {
  position: relative;
  cursor: pointer;
  user-select: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  font-size: 22px;
  border-radius: 8px;
  transition: background .2s;
}
.cart-icon:hover { background: var(--cat-primary-soft, #eff6ff); }
.cart-icon__badge {
  position: absolute;
  top: -2px;
  right: -2px;
  background: var(--cat-primary, #3b82f6);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}
</style>
