import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '../pages/HomePage.vue'
import PlaceholderPage from '../pages/PlaceholderPage.vue'
import api from '@/shared/api'

const Placeholder = (title) => ({ template: '<PlaceholderPage :title="title" />', components: { PlaceholderPage }, data: () => ({ title }) })

const routes = [
  { path: '/', name: 'home', component: HomePage, meta: { title: 'Главная' } },
  { path: '/login', component: () => import('../pages/auth/LoginMainPage.vue'), meta: { title: 'Вход' } },
  { path: '/register', component: () => import('../pages/auth/RegisterMainPage.vue'), meta: { title: 'Регистрация' } },

  // Каталоги оборудования
  { path: '/catalog/pneumatic-fittings', component: () => import('../pages/catalog/PneumaticFittingsPage.vue'), meta: { title: 'Пневмофитинги' } },
  { path: '/catalog/cable-glands', component: PlaceholderPage, props: { title: 'Кабельные вводы' }, meta: { title: 'Кабельные вводы' } },
  { path: '/catalog/pa-actuators', component: () => import('../pages/catalog/PaActuatorPage.vue'), meta: { title: 'Пневмоприводы' } },
  { path: '/catalog/gearbox', component: () => import('../pages/catalog/GearboxPage.vue'), meta: { title: 'Ручные дублёры' } },
  { path: '/catalog/ea-reducers', component: PlaceholderPage, props: { title: 'Редукторы к ЭП' }, meta: { title: 'Редукторы к ЭП', pro: true } },
  { path: '/catalog/solenoid-valves', component: () => import('../pages/catalog/SolenoidValvesPage.vue'), meta: { title: 'Соленоидные клапаны' } },
  { path: '/catalog/positioners', component: PlaceholderPage, props: { title: 'Электропневматические позиционеры' }, meta: { title: 'Позиционеры' } },
  { path: '/catalog/limit-switch', component: () => import('../pages/catalog/LimitSwitchPage.vue'), meta: { title: 'БКВ' } },
  { path: '/catalog/ea-actuators', component: PlaceholderPage, props: { title: 'Электроприводы' }, meta: { title: 'Электроприводы' } },
  { path: '/catalog/ea-cabinets', component: PlaceholderPage, props: { title: 'Шкафы управления ЭП' }, meta: { title: 'Шкафы управления ЭП', pro: true } },
  { path: '/catalog/mounting-kits', component: PlaceholderPage, props: { title: 'Монтажные комплекты и адаптации' }, meta: { title: 'Монтажные комплекты', pro: true } },
  { path: '/catalog/filter-regulator', component: () => import('../pages/catalog/FilterRegulatorPage.vue'), meta: { title: 'Фильтр-регуляторы' } },

  // Арматура
  { path: '/catalog/butterfly-valves', component: PlaceholderPage, props: { title: 'Дисковые затворы' }, meta: { title: 'Дисковые затворы' } },
  { path: '/catalog/ball-valves', component: PlaceholderPage, props: { title: 'Шаровые краны' }, meta: { title: 'Шаровые краны' } },
  { path: '/catalog/gate-valves', component: PlaceholderPage, props: { title: 'Клиновые задвижки' }, meta: { title: 'Клиновые задвижки' } },
  { path: '/catalog/knife-gate-valves', component: PlaceholderPage, props: { title: 'Шиберные задвижки' }, meta: { title: 'Шиберные задвижки' } },

  // Готовые решения
  { path: '/solutions/butterfly-pa', component: PlaceholderPage, props: { title: 'Сборки Затворов дисковых с Пневмоприводами' }, meta: { title: 'ДЗ+ПП' } },
  { path: '/solutions/ball-pa', component: PlaceholderPage, props: { title: 'Сборки Кранов шаровых с Пневмоприводами' }, meta: { title: 'ШК+ПП' } },
  { path: '/solutions/gate-pa', component: PlaceholderPage, props: { title: 'Сборки Клиновых задвижек с Пневмоприводами' }, meta: { title: 'КЗ+ПП' } },
  { path: '/solutions/knife-pa', component: PlaceholderPage, props: { title: 'Сборки Шиберных задвижек с Пневмоприводами' }, meta: { title: 'ШЗ+ПП' } },
  { path: '/solutions/butterfly-ea', component: PlaceholderPage, props: { title: 'Сборки Затворов дисковых с Электроприводами' }, meta: { title: 'ДЗ+ЭП' } },
  { path: '/solutions/ball-ea', component: PlaceholderPage, props: { title: 'Сборки Кранов шаровых с Электроприводами' }, meta: { title: 'ШК+ЭП' } },
  { path: '/solutions/gate-ea', component: PlaceholderPage, props: { title: 'Сборки Клиновых задвижек с Электроприводами' }, meta: { title: 'КЗ+ЭП' } },
  { path: '/solutions/knife-ea', component: PlaceholderPage, props: { title: 'Сборки Шиберных задвижек с Электроприводами' }, meta: { title: 'ШЗ+ЭП' } },

  // Конфигураторы (проф)
  { path: '/configurator/cabinets', component: PlaceholderPage, props: { title: 'Конфигуратор Шкафов управления ЭП' }, meta: { title: 'Шкафы ЭП', pro: true } },
  { path: '/configurator/ea-reducers', component: PlaceholderPage, props: { title: 'Конфигуратор Редукторов к ЭП' }, meta: { title: 'Редукторы к ЭП', pro: true } },
  { path: '/configurator/ea-assemblies', component: PlaceholderPage, props: { title: 'Конфигуратор Сборок арматуры с ЭП' }, meta: { title: 'Сборки с ЭП', pro: true } },
  { path: '/configurator/pa-assemblies', component: PlaceholderPage, props: { title: 'Конфигуратор Сборок арматуры с ПП' }, meta: { title: 'Сборки с ПП', pro: true } },

  // Заявки (проф)
  { path: '/requests/list', component: PlaceholderPage, props: { title: 'Список заявок' }, meta: { title: 'Заявки', pro: true } },
  { path: '/requests/contractors', component: PlaceholderPage, props: { title: 'Контрагенты' }, meta: { title: 'Контрагенты', pro: true } },

  // О проекте
  { path: '/about/contacts', component: PlaceholderPage, props: { title: 'Контакты' }, meta: { title: 'Контакты' } },

  // Администрирование
  { path: '/admin/media', component: () => import('../pages/admin/MediaPage.vue'), meta: { title: 'Медиабиблиотека', role: 'admin' } },
  { path: '/admin/cert-docs', component: () => import('../pages/admin/CertDocsPage.vue'), meta: { title: 'Сертификаты', role: 'admin' } },
  { path: '/admin/price', component: () => import('../pages/admin/PriceCatalogPage.vue'), meta: { title: 'Цены', role: 'admin' } },
  { path: '/admin/sku', component: () => import('../pages/admin/SkuAdminPage.vue'), meta: { title: 'SKU', role: 'admin' } },
  { path: '/admin/limit-switch', component: () => import('../pages/admin/LimitSwitchAdminPage.vue'), meta: { title: 'БКВ', role: 'admin' } },
  { path: '/admin/pa-constructor', component: () => import('../pages/admin/PaConstructorPage.vue'), meta: { title: 'Конструктор ПП', role: 'admin' } },
  { path: '/admin/pa-constructor-legacy', component: () => import('../pages/admin/PaConstructorLegacyPage.vue'), meta: { title: 'Конструктор ПП Old', role: 'admin' } },
  { path: '/admin/ea-constructor', component: () => import('../pages/admin/EaConstructorPage.vue'), meta: { title: 'Конструктор ЭП', role: 'admin' } },
  { path: '/admin/ea-power-supply', component: () => import('../pages/admin/EaAdminPage.vue'), meta: { title: 'Напряжения ЭП', role: 'admin' } },
  { path: '/admin/ea-switches', component: () => import('../pages/admin/EaSwitchesAdminPage.vue'), meta: { title: 'Выключатели ЭП', role: 'admin' } },
  { path: '/widgets', component: () => import('../pages/admin/WidgetsPage.vue'), meta: { title: 'Виджеты', role: 'admin' } },
  { path: '/admin/ea-models', component: () => import('../pages/admin/EaModelAdminPage.vue'), meta: { title: 'Модели ЭП', role: 'admin' } },
  { path: '/admin/ea-wirings', component: () => import('../pages/admin/EaWiringAdminPage.vue'), meta: { title: 'Схемы БУ', role: 'admin' } },
  { path: '/admin/customers', component: () => import('../pages/admin/CustomerAdminPage.vue'), meta: { title: 'Клиенты', role: 'admin' } },
  { path: '/admin/pipeline-config', component: () => import('../pages/admin/PipelineConfigPage.vue'), meta: { title: 'Pipeline Config', role: 'admin' } },
  { path: '/admin/bom-config', component: () => import('../pages/admin/BomConfigPage.vue'), meta: { title: 'BOM Config', role: 'admin' } },
  { path: '/admin/wizard-config', component: () => import('../pages/admin/WizardAdminPage.vue'), meta: { title: 'Мастер подбора', role: 'admin' } },

  // Инструменты
  { path: '/tools/image-processor', component: () => import('../pages/ImageProcessorTest.vue'), meta: { title: 'Обрезка изображений' } },
  { path: '/tools/svg-converter', component: () => import('../pages/SvgConverterTest.vue'), meta: { title: 'SVG Конвертер' } },
  { path: '/tools/pdf-to-docx', component: () => import('../pages/PdfToDocxTest.vue'), meta: { title: 'PDF → DOCX' } },
  { path: '/tools/requirements', component: () => import('../pages/RequirementsTest.vue'), meta: { title: 'Тест требований' } },
  { path: '/selector/pa', component: () => import('../pages/PaSelectionPage.vue'), meta: { title: 'Подбор ПП' } },
  { path: '/ai-assistant', component: () => import('../pages/AiAssistantPage.vue'), meta: { title: 'AI Ассистент' } },
  { path: '/ai-debug', component: () => import('../pages/AiDebugPage.vue'), meta: { title: 'AI Отладка', role: 'admin' } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to, from, next) => {
  const requiredRole = to.meta.role
  const proOnly = to.meta.pro
  if (!requiredRole && !proOnly) return next()
  try {
    const r = await api.get('/auth/me/')
    const roles = r.data.roles || []
    const isAdmin = roles.some(r => r === 'admin' || r === 'system_admin')
    if (requiredRole === 'admin' && !isAdmin) return next('/login')
    if (proOnly && roles.length === 0) return next('/login')
    next()
  } catch (e) { next('/login') }
})

export default router
