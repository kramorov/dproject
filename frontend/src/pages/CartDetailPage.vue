<!-- pages/CartDetailPage.vue -->
<template>
  <div class="cd-page">
    <div class="cd-header">
      <router-link to="/cart" class="cd-back">← К списку корзин</router-link>
    </div>

    <!-- Inline editing: name + description -->
    <div class="cd-edit">
      <input
        v-model="cartName"
        class="cd-edit__name"
        placeholder="Название корзины"
        @blur="saveName"
        @keyup.enter="$event.target.blur()"
      />
      <textarea
        v-model="cartDesc"
        class="cd-edit__desc"
        placeholder="Описание (ОЛ, объект, заметки)"
        rows="4"
        @blur="saveDesc"
      />
      <span class="cd-edit__meta" v-if="!loading">{{ items.length }} поз., {{ totalQty }} шт.</span>
    </div>

    <div v-if="loading" class="cd-loading">Загрузка...</div>
    <EmptyState v-else-if="!items.length"
      type="cart"
      title="В корзине пока нет товаров"
      text="Нажмите 🛒 на странице товара и добавляйте сюда то, что нужно."
      sub="Сохраняйте товары в разных корзинах — по объектам или проектам."
    />

    <div v-else class="cd-items">
      <EquipmentListView
        :items="items"
        :mode="viewMode"
        showModeSwitch
        @select="id => openPopup(id)"
        @update:mode="v => viewMode = v"
      >
        <template #controls="{ item }">
          <div class="cd-item__price" v-if="item.price != null">{{ item.price }} ₽</div>
          <div class="cd-item__total" v-if="item.total != null">×{{ item.quantity }} = {{ item.total }} ₽</div>
          <div class="cd-item__controls">
            <input type="number" min="1" :value="item.quantity" class="cd-qty"
              @change="e => updateQty(item.id, +e.target.value)" />
            <button class="cd-remove" title="Удалить" @click="remove(item.id)">🗑</button>
          </div>
        </template>
      </EquipmentListView>
    </div>

    <ProductDetailPopup :open="popupOpen" :itemId="popupItemId" @close="popupOpen = false" />
    <div v-if="error" class="cd-error">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import cartService from '@/shared/services/cartService'
import EmptyState from '@/shared/components/EmptyState.vue'
import EquipmentListView from '@/shared/components/catalog/EquipmentListView.vue'
import ProductDetailPopup from '@/shared/components/ProductDetailPopup.vue'
const route = useRoute()
const items = ref([])
const cartName = ref('')
const cartDesc = ref('')
const viewMode = ref('grid')
const loading = ref(true)
const error = ref('')
const popupOpen = ref(false)
const popupItemId = ref(null)
const cartId = computed(() => route.params.id)

const totalQty = computed(() => items.value.reduce((s, i) => s + i.quantity, 0))

async function load() {
  loading.value = true
  try {
    const res = await cartService.getCart(cartId.value)
    items.value = res.data?.items || []
    cartName.value = res.data?.name || ''
    cartDesc.value = res.data?.description || ''
  } catch (e) {
    error.value = 'Ошибка загрузки корзины'
  } finally {
    loading.value = false
  }
}

async function saveName() {
  try { await cartService.updateCart(cartId.value, { name: cartName.value }) }
  catch {}
}
async function saveDesc() {
  try { await cartService.updateCart(cartId.value, { description: cartDesc.value }) }
  catch {}
}

async function updateQty(itemId, qty) {
  if (qty < 1) { await remove(itemId); return }
  await cartService.updateItem(itemId, { quantity: qty })
  window.dispatchEvent(new CustomEvent('cart-updated'))
  await load()
}

async function remove(itemId) {
  await cartService.removeItem(itemId)
  window.dispatchEvent(new CustomEvent('cart-updated'))
  await load()
}

function openPopup(itemId) {
  popupItemId.value = itemId
  popupOpen.value = true
}

watch(cartId, () => { if (cartId.value) load() }, { immediate: true })
</script>

<style scoped>
.cd-page { max-width: 900px; margin: 0 auto; padding: 24px 16px; height: 100vh; display: flex; flex-direction: column; box-sizing: border-box; }
.cd-header { margin-bottom: 8px; flex-shrink: 0; }
.cd-back { font-size: 13px; color: var(--cat-primary, #3b82f6); text-decoration: none; }
.cd-back:hover { text-decoration: underline; }

/* Inline editing block */
.cd-edit { margin-bottom: 16px; flex-shrink: 0; }
.cd-edit__name {
  display: block; width: 100%; padding: 8px 12px; border: 1px solid transparent; border-radius: 6px;
  font-size: 22px; font-weight: 700; color: var(--cat-text, #1f2937); background: none;
  box-sizing: border-box; transition: border-color .15s;
}
.cd-edit__name:hover, .cd-edit__name:focus { border-color: var(--cat-border, #d1d5db); outline: none; }
.cd-edit__name:focus { border-color: var(--cat-primary, #3b82f6); }

.cd-edit__desc {
  display: block; width: 100%; padding: 6px 12px; margin-top: 4px;
  border: 1px solid transparent; border-radius: 6px;
  font-size: 14px; color: var(--cat-muted, #6b7280); background: none;
  resize: vertical; box-sizing: border-box; transition: border-color .15s;
}
.cd-edit__desc:hover, .cd-edit__desc:focus { border-color: var(--cat-border, #d1d5db); outline: none; }
.cd-edit__desc:focus { border-color: var(--cat-primary, #3b82f6); }

.cd-edit__meta { font-size: 13px; color: var(--cat-muted, #6b7280); display: block; margin-top: 4px; }

.cd-loading { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--cat-muted, #6b7280); }

/* Scrollable items area */
.cd-items { flex: 1; overflow-y: auto; min-height: 0; }

.cd-item__price { font-size: 13px; font-weight: 600; color: var(--cat-price-color, #059669); }
.cd-item__total { font-size: 12px; color: var(--cat-muted, #6b7280); }
.cd-item__controls { display: flex; align-items: center; gap: 6px; margin-top: 4px; }
.cd-qty {
  width: 52px; padding: 4px 6px; border: 1px solid #d1d5db;
  border-radius: 6px; font-size: 14px; text-align: center;
}
.cd-remove {
  background: none; border: none; cursor: pointer; font-size: 16px;
  opacity: .5; transition: opacity .2s;
}
.cd-remove:hover { opacity: 1; }

.cd-error { text-align: center; padding: 16px; color: #ef4444; background: #fef2f2; border-radius: 8px; margin-top: 16px; flex-shrink: 0; }
</style>
