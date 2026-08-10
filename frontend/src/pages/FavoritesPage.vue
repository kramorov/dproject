<!-- pages/FavoritesPage.vue -->
<template>
  <div class="fav-page">
    <div class="fav-header">
      <h2>★ Избранное</h2>
      <span class="fav-meta">{{ items.length }} поз.</span>
    </div>

    <div v-if="loading" class="fav-loading">Загрузка...</div>
    <EmptyState v-else-if="!items.length"
      type="favorites"
      title="В избранном пока нет товаров"
      text="Жмите ❤️ на странице товара и добавляйте сюда то, что нравится."
    />

    <EquipmentListView
      v-else
      :items="items"
      :mode="viewMode"
      showModeSwitch
      @select="id => openPopup(id)"
      @update:mode="v => viewMode = v"
    >
      <template #controls="{ item }">
        <div class="fav-item__price" v-if="item.price != null">{{ item.price }} ₽</div>
        <div class="fav-item__actions">
          <button class="fav-btn fav-btn--cart" title="Добавить в корзину" @click="moveToCart(item)">🛒</button>
          <button class="fav-btn fav-btn--remove" title="Удалить" @click="removeFav(item.id)">🗑</button>
        </div>
      </template>
    </EquipmentListView>

    <ProductDetailPopup :open="popupOpen" :itemId="popupItemId" @close="popupOpen = false" />
    <div v-if="error" class="fav-error">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import cartService from '@/shared/services/cartService'
import EmptyState from '@/shared/components/EmptyState.vue'
import EquipmentListView from '@/shared/components/catalog/EquipmentListView.vue'
import ProductDetailPopup from '@/shared/components/ProductDetailPopup.vue'
const items = ref([])
const viewMode = ref('grid')
const loading = ref(true)
const error = ref('')
const popupOpen = ref(false)
const popupItemId = ref(null)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await cartService.getFavorites()
    items.value = res.data?.items || []
  } catch (e) {
    error.value = 'Ошибка загрузки избранного'
  } finally {
    loading.value = false
  }
}

async function removeFav(itemId) {
  try {
    await cartService.removeItem(itemId)
    items.value = items.value.filter(i => i.id !== itemId)
    window.dispatchEvent(new CustomEvent('cart-updated'))
  } catch {}
}

async function moveToCart(item) {
  try {
    await cartService.addItem(item.sku_id)
    window.dispatchEvent(new CustomEvent('cart-updated'))
  } catch {}
}

function openPopup(itemId) {
  popupItemId.value = itemId
  popupOpen.value = true
}

onMounted(load)
</script>

<style scoped>
.fav-page { max-width: 800px; margin: 0 auto; padding: 24px 16px; }
.fav-header { display: flex; align-items: baseline; gap: 12px; margin-bottom: 20px; }
.fav-header h2 { margin: 0; font-size: 24px; }
.fav-meta { font-size: 13px; color: var(--cat-muted, #6b7280); }

.fav-loading, .fav-empty { text-align: center; padding: 40px 0; color: var(--cat-muted, #6b7280); }

.fav-item__price { font-size: 13px; font-weight: 600; color: var(--cat-price-color, #059669); }
.fav-item__actions { display: flex; gap: 6px; margin-top: 4px; }
.fav-btn {
  background: none; border: 1px solid var(--cat-border, #e5e7eb);
  border-radius: 6px; padding: 8px 12px; cursor: pointer;
  font-size: 16px; transition: all .2s;
}
.fav-btn:hover { border-color: var(--cat-primary, #3b82f6); }
.fav-btn--remove:hover { border-color: #ef4444; color: #ef4444; }

.fav-error { text-align: center; padding: 16px; color: #ef4444; background: #fef2f2; border-radius: 8px; margin-top: 16px; }
</style>
