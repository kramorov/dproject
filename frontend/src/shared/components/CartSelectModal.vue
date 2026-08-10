<!-- shared/components/CartSelectModal.vue -->
<template>
  <Transition name="modal">
    <div v-if="open" class="csm-overlay" @click.self="emit('close')">
      <div class="csm-modal">
        <h3>🛒 Выберите корзину</h3>
        <p class="csm-hint">В какую корзину добавить товар?</p>

        <div v-if="loading" class="csm-loading">Загрузка...</div>

        <div v-else-if="carts.length" class="csm-list">
          <div
            v-for="cart in carts"
            :key="cart.id"
            class="csm-card"
            :class="{ 'csm-card--active': cart.id === activeId }"
            @click="select(cart.id)"
          >
            <div class="csm-card__body">
              <span class="csm-card__name">{{ cart.name || 'Без названия' }}</span>
              <span class="csm-card__meta">{{ cart.item_count }} поз.</span>
            </div>
            <span v-if="cart.id === activeId" class="csm-card__badge">▶ активна</span>
          </div>
        </div>
        <div v-else class="csm-empty">Нет корзин</div>

        <!-- Форма создания новой -->
        <div class="csm-create">
          <h4>+ Новая корзина</h4>
          <input v-model="newName" class="csm-input" placeholder="Название (например, объект)" />
          <textarea v-model="newDesc" class="csm-input csm-textarea" placeholder="Описание (ОЛ, объект, заметки)" rows="2" />
          <button class="csm-btn csm-btn--create" :disabled="creating" @click="doCreate">
            {{ creating ? 'Создание...' : 'Создать и сделать активной' }}
          </button>
        </div>

        <button class="csm-btn csm-btn--cancel" @click="emit('close')">Отмена</button>

        <div v-if="error" class="csm-error">{{ error }}</div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, watch } from 'vue'
import cartService from '@/shared/services/cartService'

const props = defineProps({
  open: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'selected', 'created'])

const carts = ref([])
const activeId = ref(null)
const loading = ref(false)
const creating = ref(false)
const error = ref('')
const newName = ref('')
const newDesc = ref('')

async function load() {
  loading.value = true
  try {
    const res = await cartService.getActiveCartStatus()
    carts.value = (res.data || []).filter(c => c.status === 'active' && c.cart_type === 'cart')
    const active = carts.value.find(c => c.is_active_cart)
    activeId.value = active?.id || null
  } catch {
    carts.value = []
  } finally {
    loading.value = false
  }
}

async function select(id) {
  try {
    await cartService.activateCart(id)
    emit('selected', id)
    emit('close')
  } catch (e) {
    error.value = 'Ошибка выбора корзины'
  }
}

async function doCreate() {
  creating.value = true
  error.value = ''
  try {
    const res = await cartService.createCart(newName.value)
    newName.value = ''
    newDesc.value = ''
    const cartId = res.data?.id
    emit('created', cartId)
    emit('close')
  } catch (e) {
    error.value = 'Ошибка создания корзины'
  } finally {
    creating.value = false
  }
}

watch(() => props.open, (val) => {
  if (val) { newName.value = ''; newDesc.value = ''; error.value = ''; load() }
})
</script>

<style scoped>
.csm-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.4);
  z-index: 1100; display: flex; align-items: center; justify-content: center;
}
.csm-modal {
  background: #fff; padding: 24px; border-radius: 12px;
  width: 420px; max-width: 90vw; max-height: 80vh; overflow-y: auto;
}
.csm-modal h3 { margin: 0 0 4px; }
.csm-hint { font-size: 13px; color: var(--cat-muted, #6b7280); margin: 0 0 16px; }

.csm-list { display: flex; flex-direction: column; gap: 6px; margin-bottom: 16px; }
.csm-card {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 14px; border: 1px solid var(--cat-border, #e5e7eb);
  border-radius: 8px; cursor: pointer; transition: all .2s;
}
.csm-card:hover { border-color: var(--cat-primary, #3b82f6); }
.csm-card--active { border-color: var(--cat-primary, #3b82f6); background: var(--cat-primary-soft, #eff6ff); }
.csm-card__body { min-width: 0; }
.csm-card__name { display: block; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.csm-card__meta { font-size: 12px; color: var(--cat-muted, #6b7280); }
.csm-card__badge { font-size: 11px; color: var(--cat-primary, #3b82f6); font-weight: 600; flex-shrink: 0; }

.csm-create { border-top: 1px solid var(--cat-border, #e5e7eb); padding-top: 16px; margin-bottom: 12px; }
.csm-create h4 { margin: 0 0 8px; font-size: 15px; }
.csm-input {
  display: block; width: 100%; padding: 8px 12px; margin-bottom: 8px;
  border: 1px solid var(--cat-border, #e5e7eb); border-radius: 8px;
  font-size: 14px; box-sizing: border-box;
}
.csm-textarea { resize: vertical; }

.csm-btn {
  display: block; width: 100%; padding: 10px; border: none; border-radius: 8px;
  font-size: 14px; font-weight: 600; cursor: pointer; transition: opacity .2s;
}
.csm-btn:hover { opacity: .9; }
.csm-btn:disabled { opacity: .5; cursor: default; }
.csm-btn--create { background: var(--cat-primary, #3b82f6); color: #fff; }
.csm-btn--cancel { background: #f3f4f6; color: #374151; margin-top: 8px; }

.csm-loading, .csm-empty { text-align: center; padding: 16px; color: var(--cat-muted, #6b7280); }
.csm-error { text-align: center; padding: 10px; color: #ef4444; background: #fef2f2; border-radius: 8px; margin-top: 8px; }

.modal-enter-active, .modal-leave-active { transition: opacity .2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
