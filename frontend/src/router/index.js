import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '../pages/HomePage.vue'
import api from '@/shared/api'

const routes = [
  { path: '/', name: 'home', component: HomePage, meta: { title: 'Главная' } },
  { path: '/login', component: () => import('../pages/auth/LoginMainPage.vue'), meta: { title: 'Вход' } },
  { path: '/register', component: () => import('../pages/auth/RegisterMainPage.vue'), meta: { title: 'Регистрация' } },
  { path: '/catalog/gearbox', component: () => import('../pages/catalog/GearboxPage.vue'), meta: { title: 'Ручные дублёры' } },
  { path: '/catalog/filter-regulator', component: () => import('../pages/catalog/FilterRegulatorPage.vue'), meta: { title: 'Фильтр-регуляторы' } },
  { path: '/catalog/limit-switch', component: () => import('../pages/catalog/LimitSwitchPage.vue'), meta: { title: 'Блоки концевых выключателей' } },
  { path: '/admin/media', component: () => import('../pages/admin/MediaPage.vue'), meta: { title: 'Медиабиблиотека', role: 'admin' } },
  { path: '/admin/cert-docs', component: () => import('../pages/admin/CertDocsPage.vue'), meta: { title: 'Сертификаты', role: 'admin' } },
  { path: '/admin/price', component: () => import('../pages/admin/PriceCatalogPage.vue'), meta: { title: 'Цены', role: 'admin' } },
  { path: '/admin/sku', component: () => import('../pages/admin/SkuAdminPage.vue'), meta: { title: 'SKU', role: 'admin' } },
  { path: '/admin/limit-switch', component: () => import('../pages/admin/LimitSwitchAdminPage.vue'), meta: { title: 'БКВ', role: 'admin' } },
  { path: '/widgets', component: () => import('../pages/admin/WidgetsPage.vue'), meta: { title: 'Виджеты', role: 'admin' } },
  { path: '/tools/image-processor', component: () => import('../pages/ImageProcessorTest.vue'), meta: { title: 'Обрезка изображений' } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to, from, next) => {
  const requiredRole = to.meta.role
  if (!requiredRole) return next()
  try {
    const r = await api.get('/auth/me/')
    if (requiredRole === 'admin' && r.data.role !== 'admin') return next('/login')
    next()
  } catch (e) { next('/login') }
})

export default router
