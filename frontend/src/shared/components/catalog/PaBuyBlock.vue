<!-- shared/components/catalog/PaBuyBlock.vue -->
<!-- «Блок купить»: цена крупно + текстовые кнопки «В корзину» / «В избранное»
     (красный фон, без пиктограмм). Действия — те же, что были у пиктограмм. -->
<template>
  <div class="pa-buy" @click.stop>
    <div class="pa-buy__price">
      <template v-if="hasPrice">
        <span class="pa-buy__price-val">{{ price.price }}</span>
        <span class="pa-buy__price-cur">{{ price.symbol || price.currency }}</span>
      </template>
      <span v-else class="pa-buy__price-na">{{ t('catalog.engineer.priceOnRequest') }}</span>
    </div>

    <button
      type="button"
      class="pa-buy__btn"
      :class="{ 'pa-buy__btn--active': inCart }"
      :disabled="adding"
      @click="toggleCart"
    >{{ inCart ? t('catalog.buy.inCart') : t('catalog.buy.addToCart') }}</button>

    <button
      type="button"
      class="pa-buy__btn"
      :class="{ 'pa-buy__btn--active': inFavorites }"
      :disabled="adding"
      @click="toggleFavorites"
    >{{ inFavorites ? t('catalog.buy.inFavorites') : t('catalog.buy.addToFavorites') }}</button>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import cartService from '@/shared/services/cartService'
import { useI18n } from '@/shared/i18n'

const { t } = useI18n()

const props = defineProps({
  skuId: { type: Number, default: null },
  price: { type: Object, default: null },
})

const STATUS = { cartItemId: null, favItemId: null }
const inCart = ref(false)
const inFavorites = ref(false)
const adding = ref(false)

const hasPrice = computed(() =>
  !!props.price && props.price.price != null && props.price.price !== '' &&
  props.price.price !== '0' && props.price.price !== '0.00'
)

// ── Глобальный кеш статусов корзины (как в AddToCartButton) ──
const globalCache = { promise: null, data: null }

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
  if (!props.skuId) return
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
  if (!props.skuId) return
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
  if (!props.skuId) return
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

function onCartUpdated() {
  invalidateCache()
  checkStatus()
}

onMounted(checkStatus)
onMounted(() => window.addEventListener('cart-updated', onCartUpdated))
onUnmounted(() => window.removeEventListener('cart-updated', onCartUpdated))
</script>

<style scoped>
.pa-buy {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 12px;
  min-width: 200px;
  padding: 16px;
  background: var(--cat-bg, #f9fafb);
  border-radius: var(--cat-radius-lg, 12px);
}
.pa-buy__price {
  display: flex;
  align-items: baseline;
  gap: 4px;
  justify-content: center;
}
.pa-buy__price-val {
  font-size: 24px;
  font-weight: 700;
  color: var(--cat-text, #1f2937);
}
.pa-buy__price-cur {
  font-size: var(--cat-text-sm, 13px);
  color: var(--cat-muted, #6b7280);
}
.pa-buy__price-na {
  font-size: var(--cat-text-sm, 13px);
  color: var(--cat-muted, #6b7280);
}
.pa-buy__btn {
  padding: 12px 16px;
  font-size: var(--cat-text-base, 14px);
  font-weight: 600;
  color: #fff;
  background: var(--cat-buy-red, #e11d2e);
  border: none;
  border-radius: var(--cat-radius-md, 8px);
  cursor: pointer;
  transition: filter .12s;
}
.pa-buy__btn:hover {
  filter: brightness(.95);
}
.pa-buy__btn--active {
  background: var(--cat-buy-red-dark, #b91c1c);
}
.pa-buy__btn:disabled {
  opacity: .6;
  cursor: default;
}
</style>
