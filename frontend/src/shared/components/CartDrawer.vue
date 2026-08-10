<!-- shared/components/CartDrawer.vue -->
<template>
  <Transition name="drawer">
    <div v-if="open" class="cart-drawer-overlay" @click.self="emit('close')">
      <div class="cart-drawer">
        <div class="cart-drawer__header">
          <div class="cart-drawer__title-row">
            <h3>🛒 Корзина</h3>
            <button class="cart-drawer__close" @click="emit('close')">✕</button>
          </div>
          <div class="cart-drawer__selector" v-if="cartList.length > 0">
            <select v-model="activeCartId" class="cart-select" @change="switchCart">
              <option v-for="c in cartList" :key="c.id" :value="c.id">
                {{ c.name || 'Корзина ' + c.id.slice(0, 6) }}
              </option>
            </select>
            <button class="cart-drawer__new-btn" title="Новая корзина" @click="createNewCart">+</button>
          </div>
        </div>

        <div v-if="loading" class="cart-drawer__loading">Загрузка...</div>

        <div v-else-if="!items.length" class="cart-drawer__empty">
          Корзина пуста
        </div>

        <div v-else class="cart-drawer__items">
          <div
            v-for="item in items"
            :key="item.id"
            class="cart-item"
          >
            <div class="cart-item__info">
              <span class="cart-item__code">{{ item.equipment_summary?.code }}</span>
              <span class="cart-item__name">{{ item.equipment_summary?.name }}</span>
              <span class="cart-item__brand" v-if="item.equipment_summary?.brand">
                {{ item.equipment_summary.brand }}
              </span>
            </div>
            <div class="cart-item__controls">
              <input
                type="number"
                min="1"
                :value="item.quantity"
                class="cart-item__qty"
                @change="e => updateQty(item.id, +e.target.value)"
              />
              <button
                class="cart-item__remove"
                title="Удалить"
                @click="remove(item.id)"
              >🗑</button>
            </div>
          </div>
        </div>

        <div v-if="items.length" class="cart-drawer__footer">
          <div class="cart-drawer__totals">
            <span>Позиций: {{ items.length }}</span>
            <span>Всего: {{ totalQty }} шт.</span>
          </div>
          <div class="cart-drawer__actions">
            <button class="cart-btn cart-btn--export" @click="emit('export')">
              📄 Экспорт
            </button>
            <button class="cart-btn cart-btn--checkout" @click="emit('checkout', cartId)">
              Оформить заказ
            </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import cartService from '@/shared/services/cartService'

const props = defineProps({
  open: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'export', 'checkout'])

const items = ref([])
const cartId = ref(null)
const loading = ref(false)
const cartList = ref([])
const activeCartId = ref(null)

const totalQty = computed(() => items.value.reduce((s, i) => s + i.quantity, 0))

async function load() {
  loading.value = true
  try {
    const res = await cartService.getActive()
    items.value = res.data?.items || []
    cartId.value = res.data?.id || null
    activeCartId.value = cartId.value
  } catch {
    items.value = []
  } finally {
    loading.value = false
  }
}

async function loadCartList() {
  try {
    const res = await cartService.getList()
    cartList.value = (res.data || []).filter(c => c.status === 'active')
  } catch {
    cartList.value = []
  }
}

async function switchCart() {
  if (!activeCartId.value || activeCartId.value === cartId.value) return
  loading.value = true
  try {
    const res = await cartService.getCart(activeCartId.value)
    items.value = res.data?.items || []
    cartId.value = res.data?.id || null
  } catch {
    items.value = []
  } finally {
    loading.value = false
  }
}

async function createNewCart() {
  try {
    const res = await cartService.createCart()
    cartId.value = res.data?.id || null
    activeCartId.value = cartId.value
    items.value = []
    await loadCartList()
    window.dispatchEvent(new CustomEvent('cart-updated'))
  } catch (e) {
    console.error('create cart error:', e)
  }
}

async function updateQty(itemId, qty) {
  if (qty < 1) {
    await remove(itemId)
    return
  }
  await cartService.updateItem(itemId, { quantity: qty })
  window.dispatchEvent(new CustomEvent('cart-updated'))
  await load()
}

async function remove(itemId) {
  await cartService.removeItem(itemId)
  window.dispatchEvent(new CustomEvent('cart-updated'))
  await load()
}

watch(() => props.open, (val) => {
  if (val) { load(); loadCartList() }
})

onMounted(() => {
  window.addEventListener('cart-updated', load)
})
</script>

<style scoped>
.cart-drawer-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.4);
  z-index: 1000;
  display: flex; justify-content: flex-end;
}
.cart-drawer {
  width: 400px; max-width: 90vw;
  background: #fff;
  height: 100%;
  display: flex; flex-direction: column;
  box-shadow: -2px 0 12px rgba(0,0,0,.15);
}
.cart-drawer__header {
  padding: 16px 20px; border-bottom: 1px solid #e5e7eb;
}
.cart-drawer__title-row {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 8px;
}
.cart-drawer__title-row h3 { margin: 0; font-size: 18px; }
.cart-drawer__selector {
  display: flex; gap: 6px; align-items: center;
}
.cart-select {
  flex: 1; padding: 6px 8px; border: 1px solid #d1d5db; border-radius: 6px;
  font-size: 13px; background: #fff; max-width: calc(100% - 36px);
}
.cart-drawer__new-btn {
  width: 30px; height: 30px; border: 1px solid #d1d5db; border-radius: 6px;
  background: #f9fafb; font-size: 18px; font-weight: 700; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all .2s;
}
.cart-drawer__new-btn:hover { border-color: var(--cat-primary, #3b82f6); color: var(--cat-primary, #3b82f6); }
.cart-drawer__close {
  background: none; border: none; font-size: 20px; cursor: pointer;
  color: var(--cat-muted, #6b7280);
}
.cart-drawer__loading, .cart-drawer__empty {
  flex: 1; display: flex; align-items: center; justify-content: center;
  color: var(--cat-muted, #6b7280);
}
.cart-drawer__items {
  flex: 1; overflow-y: auto; padding: 12px 20px;
}
.cart-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 0; border-bottom: 1px solid #f3f4f6; gap: 12px;
}
.cart-item__info { flex: 1; min-width: 0; }
.cart-item__code {
  font-size: 12px; color: var(--cat-muted, #6b7280);
  font-family: var(--cat-font-mono, monospace); display: block;
}
.cart-item__name { font-size: 14px; display: block; margin: 2px 0; }
.cart-item__brand { font-size: 12px; color: var(--cat-muted, #6b7280); }
.cart-item__controls { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.cart-item__qty {
  width: 52px; padding: 4px 6px; border: 1px solid #d1d5db; border-radius: 6px;
  font-size: 14px; text-align: center;
}
.cart-item__remove {
  background: none; border: none; cursor: pointer; font-size: 16px;
  opacity: .5; transition: opacity .2s;
}
.cart-item__remove:hover { opacity: 1; }

.cart-drawer__footer {
  border-top: 1px solid #e5e7eb; padding: 16px 20px;
}
.cart-drawer__totals {
  display: flex; justify-content: space-between;
  font-size: 14px; color: var(--cat-muted, #6b7280); margin-bottom: 12px;
}
.cart-drawer__actions { display: flex; gap: 8px; }
.cart-btn {
  flex: 1; padding: 10px 16px; border: none; border-radius: 8px;
  font-size: 14px; font-weight: 600; cursor: pointer;
  transition: opacity .2s;
}
.cart-btn:hover { opacity: .9; }
.cart-btn--export { background: #f3f4f6; color: #374151; }
.cart-btn--checkout { background: var(--cat-primary, #3b82f6); color: #fff; }

.drawer-enter-active, .drawer-leave-active { transition: transform .3s ease, opacity .3s ease; }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
.drawer-enter-from .cart-drawer, .drawer-leave-to .cart-drawer { transform: translateX(100%); }
</style>
