<!-- pages/CartListPage.vue -->
<template>
  <div class="cart-list-page">
    <div class="clp-header">
      <h2>🛒 Мои корзины</h2>
      <button class="clp-btn clp-btn--new" @click="createNew">+ Новая корзина</button>
    </div>

    <div v-if="loading" class="clp-loading">Загрузка...</div>
    <div v-else-if="!carts.length" class="clp-empty">Нет активных корзин</div>

    <div v-else class="clp-grid">
      <div v-for="cart in carts" :key="cart.id" class="clp-card" :class="{ 'clp-card--active': cart.is_active_cart }" @click="openCart(cart.id)">
        <div class="clp-card__header">
          <h3>
            <span v-if="cart.is_active_cart" class="clp-active-mark">▶</span>
            {{ cart.name || 'Без названия' }}
          </h3>
          <span class="clp-card__badge" :class="'clp-badge--' + cart.status">
            {{ cart.is_active_cart ? 'Активна' : (statusLabels[cart.status] || cart.status) }}
          </span>
        </div>
        <div class="clp-card__meta">
          <span>{{ cart.item_count }} поз.</span>
          <span>{{ formatDate(cart.updated_at) }}</span>
        </div>
        <div class="clp-card__actions" @click.stop>
          <button v-if="!cart.is_active_cart" class="clp-card__btn" title="Сделать активной" @click="activateCart(cart.id)">▶</button>
          <button class="clp-card__btn clp-card__btn--danger" title="Удалить" @click="removeCart(cart.id)">🗑</button>
        </div>
      </div>
    </div>

    <div v-if="error" class="clp-error">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import cartService from '@/shared/services/cartService'

const router = useRouter()
const carts = ref([])
const loading = ref(true)
const error = ref('')

const statusLabels = { active: 'Активна', ordered: 'Оформлена', abandoned: 'Удалена' }

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await cartService.getList()
    carts.value = (res.data || []).filter(c => c.status !== 'abandoned')
  } catch (e) {
    error.value = 'Ошибка загрузки корзин'
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function createNew() {
  try {
    await cartService.createCart()
    window.dispatchEvent(new CustomEvent('cart-updated'))
    await load()
  } catch (e) {
    error.value = 'Ошибка создания корзины'
  }
}

function openCart(id) {
  router.push(`/cart/${id}`)
}

async function activateCart(id) {
  try {
    await cartService.activateCart(id)
    window.dispatchEvent(new CustomEvent('cart-updated'))
    await load()
  } catch (e) {
    error.value = 'Ошибка активации корзины'
  }
}

async function removeCart(id) {
  if (!confirm('Удалить корзину?')) return
  try {
    await cartService.deleteCart(id)
    carts.value = carts.value.filter(c => c.id !== id)
    window.dispatchEvent(new CustomEvent('cart-updated'))
  } catch (e) {
    error.value = 'Ошибка удаления корзины'
  }
}

onMounted(load)
</script>

<style scoped>
.cart-list-page { max-width: 800px; margin: 0 auto; padding: 24px 16px; }
.clp-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.clp-header h2 { margin: 0; font-size: 24px; }

.clp-btn { padding: 8px 16px; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; }
.clp-btn--new { background: var(--cat-primary, #3b82f6); color: #fff; }
.clp-btn--cancel { background: #f3f4f6; color: #374151; }
.clp-btn--save { background: var(--cat-primary, #3b82f6); color: #fff; }

.clp-loading, .clp-empty { text-align: center; padding: 40px 0; color: var(--cat-muted, #6b7280); }

.clp-grid { display: flex; flex-direction: column; gap: 8px; }

.clp-card {
  display: flex; align-items: center; gap: 16px;
  padding: 16px 20px;
  border: 1px solid var(--cat-border, #e5e7eb);
  border-radius: 10px;
  background: #fff;
  cursor: pointer;
  transition: box-shadow .2s, border-color .2s;
}
.clp-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,.08); border-color: var(--cat-primary, #3b82f6); }
.clp-card--active { border-color: var(--cat-primary, #3b82f6); background: var(--cat-primary-soft, #eff6ff); }

.clp-active-mark { color: var(--cat-primary, #3b82f6); font-size: 12px; margin-right: 4px; }

.clp-card__header { flex: 1; min-width: 0; }
.clp-card__header h3 { margin: 0; font-size: 16px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.clp-card__badge {
  font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600;
}
.clp-badge--active { background: #ecfdf5; color: #059669; }

.clp-card__meta {
  font-size: 12px; color: var(--cat-muted, #6b7280);
  display: flex; flex-direction: column; align-items: flex-end; gap: 2px;
  flex-shrink: 0;
}

.clp-card__actions { display: flex; gap: 4px; flex-shrink: 0; }
.clp-card__btn {
  background: none; border: 1px solid transparent; border-radius: 6px;
  padding: 4px 8px; cursor: pointer; font-size: 16px; transition: all .2s;
}
.clp-card__btn:hover { border-color: var(--cat-border, #e5e7eb); }
.clp-card__btn--danger:hover { border-color: #ef4444; color: #ef4444; }

/* Модалка */
.clp-modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.4);
  z-index: 1000; display: flex; align-items: center; justify-content: center;
}
.clp-modal {
  background: #fff; padding: 24px; border-radius: 12px; width: 360px; max-width: 90vw;
}
.clp-modal h4 { margin: 0 0 12px; }
.clp-input {
  width: 100%; padding: 8px 12px; border: 1px solid var(--cat-border, #e5e7eb);
  border-radius: 8px; font-size: 14px; box-sizing: border-box;
}
.clp-modal__btns { display: flex; gap: 8px; margin-top: 16px; justify-content: flex-end; }

.clp-error {
  text-align: center; padding: 16px; color: #ef4444; background: #fef2f2;
  border-radius: 8px; margin-top: 16px;
}
</style>
