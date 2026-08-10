<!-- shared/components/AddToCartButton.vue -->
<template>
  <div class="cart-actions" @click.stop>
    <button
      class="cart-btn cart-btn--cart"
      :class="{ 'cart-btn--active': inCart }"
      :title="inCart ? 'В корзине' : 'Добавить в корзину'"
      @click="toggleCart"
    >
      <span v-if="adding" class="spinner"></span>
      <span v-else>{{ inCart ? '🛒✓' : '🛒' }}</span>
    </button>
    <button
      class="cart-btn cart-btn--fav"
      :class="{ 'cart-btn--active': inFavorites }"
      :title="inFavorites ? 'В избранном' : 'Добавить в избранное'"
      @click="toggleFavorites"
    >
      <span>{{ inFavorites ? '★' : '☆' }}</span>
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import cartService from '@/shared/services/cartService'

const props = defineProps({
  skuId: { type: Number, required: true },
})

const STATUS = {
  cartItemId: null,
  favItemId: null,
}

const inCart = ref(false)
const inFavorites = ref(false)
const adding = ref(false)

// ── Глобальный кеш статусов корзины ──
const globalCache = {
  promise: null,
  data: null,
}

async function fetchCartStatus() {
  if (globalCache.promise) return globalCache.promise
  globalCache.promise = Promise.all([
    cartService.getActive().catch(() => ({ data: { items: [] } })),
    cartService.getFavorites().catch(() => ({ data: { items: [] } })),
  ]).then(([cartRes, favRes]) => {
    globalCache.data = {
      cartItems: cartRes.data?.items || [],
      favItems: favRes.data?.items || [],
    }
    return globalCache.data
  })
  return globalCache.promise
}

function invalidateCache() {
  globalCache.promise = null
  globalCache.data = null
}

async function checkStatus() {
  try {
    const { cartItems, favItems } = await fetchCartStatus()
    const cartFound = cartItems.find(i => i.sku_id === props.skuId)
    const favFound = favItems.find(i => i.sku_id === props.skuId)

    inCart.value = !!cartFound
    inFavorites.value = !!favFound
    if (cartFound) STATUS.cartItemId = cartFound.id
    if (favFound) STATUS.favItemId = favFound.id
  } catch {}
}

async function toggleCart() {
  adding.value = true
  try {
    if (inCart.value && STATUS.cartItemId) {
      await cartService.removeItem(STATUS.cartItemId)
      inCart.value = false
      STATUS.cartItemId = null
    } else {
      const res = await cartService.addItem(props.skuId)
      inCart.value = true
      STATUS.cartItemId = res.data?.item?.id || null
    }
  } catch (e) {
    console.error('cart toggle error:', e)
  } finally {
    adding.value = false
    invalidateCache()
    window.dispatchEvent(new CustomEvent('cart-updated'))
  }
}

async function toggleFavorites() {
  adding.value = true
  try {
    if (inFavorites.value && STATUS.favItemId) {
      await cartService.removeItem(STATUS.favItemId)
      inFavorites.value = false
      STATUS.favItemId = null
    } else {
      const res = await cartService.addToFavorites(props.skuId)
      inFavorites.value = true
      STATUS.favItemId = res.data?.item?.id || null
    }
  } catch (e) {
    console.error('fav toggle error:', e)
  } finally {
    adding.value = false
    invalidateCache()
    window.dispatchEvent(new CustomEvent('cart-updated'))
  }
}

onMounted(checkStatus)

// Глобальный слушатель — инвалидировать кеш при изменении корзины
function onCartUpdated() {
  invalidateCache()
  checkStatus()
}
onMounted(() => window.addEventListener('cart-updated', onCartUpdated))
onUnmounted(() => window.removeEventListener('cart-updated', onCartUpdated))
</script>

<style scoped>
.cart-actions {
  display: flex;
  gap: 4px;
  align-items: center;
}
.cart-btn {
  background: none;
  border: 1px solid var(--cat-border, #e5e7eb);
  border-radius: 6px;
  padding: 2px 8px;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  transition: all .2s;
  opacity: 0.6;
}
.cart-btn:hover { opacity: 1; border-color: var(--cat-primary, #3b82f6); }
.cart-btn--active { opacity: 1; border-color: var(--cat-primary, #3b82f6); background: var(--cat-primary-soft, #eff6ff); }
.spinner {
  display: inline-block;
  width: 12px; height: 12px;
  border: 2px solid var(--cat-border, #e5e7eb);
  border-top-color: var(--cat-primary, #3b82f6);
  border-radius: 50%;
  animation: spin .6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
