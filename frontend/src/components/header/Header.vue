<template>
  <header class="site-header">
    <div class="header-left"><router-link to="/" class="logo">На главную</router-link></div>
    <nav class="header-nav"><TopMenu /></nav>
    <div class="header-actions">
      <!-- Корзина: клик → список, ховер → дропдаун -->
      <div class="hdr-cart"
        @click="goToCartList"
        @mouseenter="openDropdown"
        @mouseleave="scheduleClose"
        ref="cartRef"
      >
        <svg class="hdr-cart__icon" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/>
          <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
        </svg>
        <span v-if="cartCount" class="hdr-cart__badge">{{ cartCount }}</span>

        <!-- Дропдаун -->
        <Transition name="hdr-dd">
          <div v-if="dropdownOpen" class="hdr-cart__dropdown"
            @mouseenter="cancelClose"
            @mouseleave="scheduleClose"
            @click.stop
          >
            <div class="hdr-dd__title">Мои корзины</div>
            <div v-if="dropdownCarts.length" class="hdr-dd__list">
              <router-link
                v-for="c in dropdownCarts"
                :key="c.id"
                :to="`/cart/${c.id}`"
                class="hdr-dd__item"
                :class="{ 'hdr-dd__item--active': c.is_active_cart }"
                @click="selectCart(c)"
              >
                <span class="hdr-dd__name">{{ c.name || 'Без названия' }}</span>
                <span class="hdr-dd__count">{{ c.item_count }} поз.</span>
              </router-link>
            </div>
            <div v-else class="hdr-dd__empty">Нет корзин</div>
            <button class="hdr-dd__new" @click="createAndOpen">+ Новая корзина</button>
          </div>
        </Transition>
      </div>

      <!-- Избранное -->
      <router-link to="/favorites" class="hdr-fav" title="Избранное">
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
        </svg>
      </router-link>
    </div>
    <div class="header-right">
      <template v-if="user">
        <span class="user-name">{{ user.username }}</span>
        <button class="logout-btn" @click="doLogout">Выход</button>
      </template>
      <router-link v-else to="/login" class="auth-link">Вход</router-link>
    </div>
  </header>
</template>
<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import TopMenu from './TopMenu.vue'
import AppButton from '@/shared/components/AppButton.vue'
import { useAuth } from './useAuth.js'
import cartService from '@/shared/services/cartService'
import api from '@/shared/api'
const { user, role } = useAuth()

const router = useRouter()
const cartCount = ref(0)
const dropdownOpen = ref(false)
const dropdownCarts = ref([])
const cartRef = ref(null)
let closeTimer = null

async function updateCartCount() {
  try {
    const res = await cartService.getActive()
    cartCount.value = res.data?.total_quantity || res.data?.item_count || 0
  } catch { cartCount.value = 0 }
}

async function loadDropdownCarts() {
  try {
    const res = await cartService.getList()
    dropdownCarts.value = (res.data || []).filter(c => c.status === 'active' && c.cart_type === 'cart')
  } catch { dropdownCarts.value = [] }
}

function openDropdown() {
  cancelClose()
  dropdownOpen.value = true
  loadDropdownCarts()
}

function scheduleClose() {
  closeTimer = setTimeout(() => { dropdownOpen.value = false }, 200)
}

function cancelClose() {
  if (closeTimer) { clearTimeout(closeTimer); closeTimer = null }
}

function goToCartList() {
  dropdownOpen.value = false
  router.push('/cart')
}

async function selectCart(cart) {
  if (!cart.is_active_cart) {
    try { await cartService.activateCart(cart.id) } catch {}
    window.dispatchEvent(new CustomEvent('cart-updated'))
  }
  dropdownOpen.value = false
}

async function createAndOpen() {
  try {
    const res = await cartService.createCart()
    const newId = res.data?.id
    dropdownOpen.value = false
    if (newId) router.push(`/cart/${newId}`)
  } catch {}
}

function onCartUpdated() { updateCartCount() }

onMounted(() => {
  updateCartCount()
  window.addEventListener('cart-updated', onCartUpdated)
})
onUnmounted(() => {
  window.removeEventListener('cart-updated', onCartUpdated)
})

async function doLogout() {
  try { await api.post('/auth/logout/') } catch(e) {}
  user.value = null
  role.value = 'viewer'
  window.location.href = '/'
}
</script>
<style scoped>
.site-header{display:flex;align-items:center;justify-content:space-between;background:var(--site-header-bg);color:var(--site-header-text);padding:0 20px;height:56px;gap:16px}
.header-left{flex-shrink:0}
.logo{font-size:18px;font-weight:700;color:inherit;text-decoration:none}
.header-nav{flex:1}
.header-actions{display:flex;align-items:center;gap:2px;flex-shrink:0}
.header-right{display:flex;align-items:center;gap:12px;flex-shrink:0}
.user-name{font-size:13px;opacity:.9}
.logout-btn{background:rgba(255,255,255,.15);color:#fff;border:1px solid rgba(255,255,255,.25);padding:5px 14px;border-radius:var(--cat-radius-md,6px);cursor:pointer;font-size:13px}
.logout-btn:hover{background:rgba(255,255,255,.25)}
.auth-link{color:inherit;text-decoration:none;font-size:14px;padding:6px 12px;border-radius:4px;transition:background .15s}
.auth-link:hover{background:rgba(255,255,255,.15)}

/* Корзина */
.hdr-cart{position:relative;display:flex;align-items:center;justify-content:center;width:40px;height:40px;color:inherit;cursor:pointer;border-radius:8px;transition:background .15s}
.hdr-cart:hover{background:rgba(255,255,255,.15)}
.hdr-cart__badge{position:absolute;top:2px;right:2px;background:#ef4444;color:#fff;font-size:10px;font-weight:700;min-width:18px;height:18px;border-radius:9px;display:flex;align-items:center;justify-content:center;padding:0 4px;line-height:1}

/* Дропдаун */
.hdr-cart__dropdown{position:absolute;top:100%;right:0;min-width:280px;background:#fff;border:1px solid #e5e7eb;border-radius:10px;box-shadow:0 8px 30px rgba(0,0,0,.12);z-index:200;padding:8px 0;margin-top:4px}
.hdr-dd__title{font-size:13px;font-weight:600;color:#374151;padding:6px 16px 10px;border-bottom:1px solid #f3f4f6}
.hdr-dd__list{max-height:240px;overflow-y:auto}
.hdr-dd__item{display:flex;justify-content:space-between;align-items:center;padding:8px 16px;font-size:13px;color:#1f2937;text-decoration:none;transition:background .1s}
.hdr-dd__item:hover{background:#f9fafb}
.hdr-dd__item--active .hdr-dd__name{font-weight:700;color:var(--cat-primary,#3b82f6)}
.hdr-dd__name{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hdr-dd__count{font-size:11px;color:#9ca3af;margin-left:8px;flex-shrink:0}
.hdr-dd__empty{padding:12px 16px;font-size:13px;color:#9ca3af}
.hdr-dd__new{display:block;width:100%;padding:8px 16px;border:none;border-top:1px solid #f3f4f6;background:none;font-size:13px;color:var(--cat-primary,#3b82f6);cursor:pointer;text-align:left;margin-top:4px;transition:background .1s}
.hdr-dd__new:hover{background:#f9fafb}

/* Transition */
.hdr-dd-enter-active,.hdr-dd-leave-active{transition:opacity .15s,transform .15s}
.hdr-dd-enter-from,.hdr-dd-leave-to{opacity:0;transform:translateY(-4px)}

/* Избранное */
.hdr-fav{display:flex;align-items:center;justify-content:center;width:40px;height:40px;color:inherit;text-decoration:none;border-radius:8px;transition:background .15s,color .15s}
.hdr-fav:hover{background:rgba(255,255,255,.15);color:#f87171}
</style>
