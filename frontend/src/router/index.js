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
  { path: '/catalog/solenoid-valves', component: () => import('../pages/catalog/SolenoidValvesPage.vue'), meta: { title: 'Распределительные клапаны' } },
  { path: '/catalog/pneumatic-fittings', component: () => import('../pages/catalog/PneumaticFittingsPage.vue'), meta: { title: 'Пневматические фитинги' } },
  { path: '/admin/media', component: () => import('../pages/admin/MediaPage.vue'), meta: { title: 'Медиабиблиотека', role: 'admin' } },
  { path: '/admin/cert-docs', component: () => import('../pages/admin/CertDocsPage.vue'), meta: { title: 'Сертификаты', role: 'admin' } },
  { path: '/admin/price', component: () => import('../pages/admin/PriceCatalogPage.vue'), meta: { title: 'Цены', role: 'admin' } },
  { path: '/admin/sku', component: () => import('../pages/admin/SkuAdminPage.vue'), meta: { title: 'SKU', role: 'admin' } },
  { path: '/admin/limit-switch', component: () => import('../pages/admin/LimitSwitchAdminPage.vue'), meta: { title: 'БКВ', role: 'admin' } },
  { path: '/admin/pa-constructor', component: () => import('../pages/admin/PaConstructorPage.vue'), meta: { title: 'Конструктор пневмоприводов', role: 'admin' } },
  { path: '/admin/ea-constructor', component: () => import('../pages/admin/EaConstructorPage.vue'), meta: { title: 'Конструктор электроприводов', role: 'admin' } },
  { path: '/admin/ea-power-supply', component: () => import('../pages/admin/EaAdminPage.vue'), meta: { title: 'Опции напряжения ЭП', role: 'admin' } },
  { path: '/admin/ea-switches', component: () => import('../pages/admin/EaSwitchesAdminPage.vue'), meta: { title: 'Опции выключателей ЭП', role: 'admin' } },
  { path: '/widgets', component: () => import('../pages/admin/WidgetsPage.vue'), meta: { title: 'Виджеты', role: 'admin' } },
  { path: '/admin/ea-models', component: () => import('../pages/admin/EaModelAdminPage.vue'), meta: { title: 'Модели ЭП', role: 'admin' } },
  { path: '/admin/ea-wirings', component: () => import('../pages/admin/EaWiringAdminPage.vue'), meta: { title: 'Схемы БУ', role: 'admin' } },
  { path: '/admin/customers', component: () => import('../pages/admin/CustomerAdminPage.vue'), meta: { title: 'Клиенты', role: 'admin' } },
  { path: '/tools/image-processor', component: () => import('../pages/ImageProcessorTest.vue'), meta: { title: 'Обрезка изображений' } },
  { path: '/tools/svg-converter', component: () => import('../pages/SvgConverterTest.vue'), meta: { title: 'SVG Конвертер' } },
  { path: '/tools/pdf-to-docx', component: () => import('../pages/PdfToDocxTest.vue'), meta: { title: 'PDF → DOCX' } },
  { path: '/tools/requirements', component: () => import('../pages/RequirementsTest.vue'), meta: { title: 'Тест требований' } },
  { path: '/selector/pa', component: () => import('../pages/PaSelectionPage.vue'), meta: { title: 'Подбор пневмопривода' } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to, from, next) => {
  const requiredRole = to.meta.role
  if (!requiredRole) return next()
  try {
    const r = await api.get('/auth/me/')
    const roles = r.data.roles || []
    if (requiredRole === 'admin' && !roles.includes('admin')) return next('/login')
    next()
  } catch (e) { next('/login') }
})

export default router