// shared/services/cartService.js
// API-сервис для корзины и избранного.
import api from '@/shared/api'
import { ENDPOINTS } from '@/shared/endpoints'

const E = ENDPOINTS.cart || {}
const B = '/cart'  // base prefix (axios already has /api)

export default {
  // ── корзина ──
  getActive()     { return api.get(E.active || `${B}/active/`) },
  getList()       { return api.get(E.list || `${B}/`) },
  getCart(id)     { return api.get(`${E.list || `${B}/`}${id}/`) },

  addItem(skuId, quantity = 1, cartType = 'cart') {
    return api.post(E.add || `${B}/add/`, {
      sku_id: skuId, quantity, cart_type: cartType,
    })
  },

  updateItem(itemId, data) {
    return api.patch(`${E.items || `${B}/items/`}${itemId}/update/`, data)
  },

  removeItem(itemId) {
    return api.delete(`${E.items || `${B}/items/`}${itemId}/`)
  },

  // ── избранное ──
  getFavorites()  { return api.get(E.favorites || `${B}/favorites/`) },

  addToFavorites(skuId) {
    return this.addItem(skuId, 1, 'favorites')
  },

  // ── управление корзинами ──
  createCart(name = '') {
    return api.post(`${B}/create/`, { name })
  },

  updateCart(cartId, data) {
    return api.patch(`${B}/${cartId}/manage/`, data)
  },

  deleteCart(cartId) {
    return api.delete(`${B}/${cartId}/manage/`)
  },

  activateCart(cartId) {
    return api.post(`${B}/${cartId}/activate/`)
  },

  getActiveCartStatus() {
    return api.get(`${B}/`)
  },

  // ── деталировка товара (для popup) ──
  getItemDetail(itemId) {
    return api.get(`${B}/items/${itemId}/detail/`)
  },

  // ── оформление ──
  checkout(cartId, data = {}) {
    return api.post(E.checkout || `${B}/checkout/`, { cart_id: cartId, ...data })
  },
}
