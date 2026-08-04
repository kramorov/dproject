import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '../pages/HomePage.vue'
import PlaceholderPage from '../pages/PlaceholderPage.vue'
import api from '@/shared/api'

const Placeholder = (title) => ({ template: '<PlaceholderPage :title="title" />', components: { PlaceholderPage }, data: () => ({ title }) })


// Sections accessible without authentication (public catalog pages)
const PUBLIC_SECTIONS = [
  'catalog_gearbox', 'catalog_pa', 'catalog_ea', 'catalog_lsb',
  'catalog_sv', 'catalog_fr', 'catalog_pf', 'catalog_cg',
]

const routes = [
  { path: '/', name: 'home', component: HomePage, meta: { title: 'Главная' } },
  { path: '/login', component: () => import('../pages/auth/LoginMainPage.vue'), meta: { title: 'Вход' } },
  { path: '/register', component: () => import('../pages/auth/RegisterMainPage.vue'), meta: { title: 'Регистрация' } },

  // Каталоги оборудования
  // Каталоги — индексные страницы
  { path: '/catalogs/equipment', name: 'catalogs-equipment', component: () => import('../pages/catalog/CatalogEquipmentIndex.vue'), meta: { title: 'Каталоги оборудования' } },
  { path: '/catalogs/valves', name: 'catalogs-valves', component: () => import('../pages/catalog/CatalogValvesIndex.vue'), meta: { title: 'Каталоги арматуры' } },
  { path: '/catalogs/solutions', name: 'catalogs-solutions', component: () => import('../pages/catalog/CatalogSolutionsIndex.vue'), meta: { title: 'Каталог готовых решений' } },

  { path: '/catalog/pneumatic-fittings', component: () => import('../pages/catalog/PneumaticFittingsPage.vue'), meta: { title: 'Пневмофитинги', section: 'catalog_pf' } },
  { path: '/catalog/cable-glands', component: PlaceholderPage, props: { title: 'Кабельные вводы' }, meta: { title: 'Кабельные вводы', section: 'catalog_cg' } },
  { path: '/catalog/pa-actuators', component: () => import('../pages/catalog/PaActuatorPage.vue'), meta: { title: 'Пневмоприводы', section: 'catalog_pa' } },
  { path: '/catalog/gearbox', component: () => import('../pages/catalog/GearboxPage.vue'), meta: { title: 'Ручные дублёры', section: 'catalog_gearbox' } },
  { path: '/catalog/ea-reducers', component: PlaceholderPage, props: { title: 'Редукторы к ЭП' }, meta: { title: 'Редукторы к ЭП' } },
  { path: '/catalog/solenoid-valves', component: () => import('../pages/catalog/SolenoidValvesPage.vue'), meta: { title: 'Соленоидные клапаны', section: 'catalog_sv' } },
  { path: '/catalog/positioners', component: PlaceholderPage, props: { title: 'Электропневматические позиционеры' }, meta: { title: 'Позиционеры' } },
  { path: '/catalog/limit-switch', component: () => import('../pages/catalog/LimitSwitchPage.vue'), meta: { title: 'БКВ', section: 'catalog_lsb' } },
  { path: '/catalog/ea-actuators', component: PlaceholderPage, props: { title: 'Электроприводы' }, meta: { title: 'Электроприводы', section: 'catalog_ea' } },
  { path: '/catalog/ea-cabinets', component: PlaceholderPage, props: { title: 'Шкафы управления ЭП' }, meta: { title: 'Шкафы управления ЭП', pro: true } },
  { path: '/catalog/mounting-kits', component: PlaceholderPage, props: { title: 'Монтажные комплекты и адаптации' }, meta: { title: 'Монтажные комплекты', pro: true } },
  { path: '/catalog/filter-regulator', component: () => import('../pages/catalog/FilterRegulatorPage.vue'), meta: { title: 'Фильтр-регуляторы', section: 'catalog_fr' } },

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
  { path: '/configurator/cabinets', component: PlaceholderPage, props: { title: 'Конфигуратор Шкафов управления ЭП' }, meta: { title: 'Шкафы ЭП' } },
  { path: '/configurator/ea-reducers', component: PlaceholderPage, props: { title: 'Конфигуратор Редукторов к ЭП' }, meta: { title: 'Редукторы к ЭП' } },
  { path: '/configurator/ea-assemblies', component: PlaceholderPage, props: { title: 'Конфигуратор Сборок арматуры с ЭП' }, meta: { title: 'Сборки с ЭП' } },
  { path: '/configurator/pa-assemblies', component: PlaceholderPage, props: { title: 'Конфигуратор Сборок арматуры с ПП' }, meta: { title: 'Сборки с ПП' } },

  // Заявки (проф)
  { path: '/requests/list', component: PlaceholderPage, props: { title: 'Список заявок' }, meta: { title: 'Заявки', pro: true } },
  { path: '/requests/contractors', component: PlaceholderPage, props: { title: 'Контрагенты' }, meta: { title: 'Контрагенты', pro: true } },

  // О проекте
  { path: '/about', name: 'about', component: () => import('../pages/about/AboutIndex.vue'), meta: { title: 'О проекте' } },
  { path: '/about/capabilities', name: 'about-capabilities', component: () => import('../pages/about/AboutSection.vue'), meta: { title: 'Возможности системы' } },
  { path: '/about/benefits-users', name: 'about-benefits-users', component: () => import('../pages/about/AboutSection.vue'), meta: { title: 'Преимущества для пользователей' } },
  { path: '/about/benefits-types', name: 'about-benefits-types', component: () => import('../pages/about/AboutSection.vue'), meta: { title: 'Преимущества по типам потребителей' } },
  { path: '/about/architecture', name: 'about-architecture', component: () => import('../pages/about/AboutSection.vue'), meta: { title: 'Архитектура системы' } },
  { path: '/about/contacts', component: PlaceholderPage, props: { title: 'Контакты' }, meta: { title: 'Контакты' } },

  // Администрирование — разделы каталога (catalog)
  { path: '/admin/media', component: () => import('../pages/admin/MediaPage.vue'), meta: { title: 'Медиабиблиотека', section: 'admin_section' } },
  { path: '/admin/cert-docs', component: () => import('../pages/admin/CertDocsPage.vue'), meta: { title: 'Сертификаты', section: 'certificates' } },
  { path: '/admin/price', component: () => import('../pages/admin/PriceCatalogPage.vue'), meta: { title: 'Цены', section: 'admin_section' } },
  { path: '/admin/sku', component: () => import('../pages/admin/SkuAdminPage.vue'), meta: { title: 'SKU', section: 'admin_section' } },
  { path: '/admin/limit-switch', component: () => import('../pages/admin/LimitSwitchAdminPage.vue'), meta: { title: 'БКВ', section: 'admin_section' } },
  { path: '/widgets', component: () => import('../pages/admin/WidgetsPage.vue'), meta: { title: 'Виджеты', section: 'admin_section' } },

  // Администрирование — конфигураторы (configurator)
  { path: '/configurator/pa', component: () => import('../pages/admin/PaConstructorPage.vue'), meta: { title: 'Конструктор ПП', section: 'configurator_pa' } },
  { path: '/configurator/pa-legacy', component: () => import('../pages/admin/PaConstructorLegacyPage.vue'), meta: { title: 'Конструктор ПП Old', section: 'configurator_pa' } },
  { path: '/admin/ea-constructor', component: () => import('../pages/admin/EaConstructorPage.vue'), meta: { title: 'Конструктор ЭП', section: 'configurator_ea' } },
  { path: '/admin/ea-power-supply', component: () => import('../pages/admin/EaAdminPage.vue'), meta: { title: 'Напряжения ЭП', section: 'configurator_ea' } },
  { path: '/admin/ea-switches', component: () => import('../pages/admin/EaSwitchesAdminPage.vue'), meta: { title: 'Выключатели ЭП', section: 'configurator_ea' } },
  { path: '/admin/ea-models', component: () => import('../pages/admin/EaModelAdminPage.vue'), meta: { title: 'Модели ЭП', section: 'configurator_ea' } },
  { path: '/admin/ea-wirings', component: () => import('../pages/admin/EaWiringAdminPage.vue'), meta: { title: 'Схемы БУ', section: 'configurator_ea' } },

  // Администрирование — только для admin/staff
  { path: '/admin/customers', component: () => import('../pages/admin/CustomerAdminPage.vue'), meta: { title: 'Клиенты', object: 'admin.customers', action: 'edit' } },
  { path: '/admin/pipeline-config', component: () => import('../pages/admin/PipelineConfigPage.vue'), meta: { title: 'Pipeline Config', object: 'ai.pipelines', action: 'edit' } },
  { path: '/admin/skill-config', component: () => import('../pages/admin/SkillConfigPage.vue'), meta: { title: 'Skill Config', object: 'ai.skills', action: 'edit' } },
  { path: '/admin/wizard-config', component: () => import('../pages/admin/WizardAdminPage.vue'), meta: { title: 'Мастер подбора', object: 'ai.wizard', action: 'edit' } },
  { path: '/admin/permissions', component: () => import('../pages/admin/PermissionsPage.vue'), meta: { title: 'Права доступа', object: 'admin.permissions', action: 'edit' } },

  // Инструменты
  { path: '/tools/image-processor', component: () => import('../pages/ImageProcessorTest.vue'), meta: { title: 'Обрезка изображений' } },
  { path: '/tools/svg-converter', component: () => import('../pages/SvgConverterTest.vue'), meta: { title: 'SVG Конвертер' } },
  { path: '/tools/pdf-to-docx', component: () => import('../pages/PdfToDocxTest.vue'), meta: { title: 'PDF → DOCX' } },
  { path: '/tools/requirements', component: () => import('../pages/RequirementsTest.vue'), meta: { title: 'Тест требований' } },
  { path: '/selector/pa', component: () => import('../pages/PaSelectionPage.vue'), meta: { title: 'Подбор ПП', section: 'configurator_pa' } },
  { path: '/ai-assistant', component: () => import('../pages/AiAssistantPage.vue'), meta: { title: 'AI Ассистент' } },
  { path: '/ai-debug', component: () => import('../pages/AiDebugPage.vue'), meta: { title: 'AI Отладка', object: 'ai.debug', action: 'view' } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to, from, next) => {
  const requiredObject = to.meta.object
  const requiredAction = to.meta.action || 'view'
  const requiredRole = to.meta.role
  const requiredSection = to.meta.section
  const proOnly = to.meta.pro
  if (!requiredObject && !requiredRole && !requiredSection && !proOnly) return next()

  // Try to get user info; unauthenticated -> only PUBLIC_SECTIONS allowed
  let r
  try {
    r = await api.get('/auth/me/')
  } catch (e) {
    if (requiredSection && PUBLIC_SECTIONS.includes(requiredSection)) return next()
    if (!requiredObject && !requiredRole && !proOnly) return next()
    return next('/login')
  }

  try {
    const objPerms = r.data.object_permissions || {}
    const roles = r.data.roles || []
    const sections = r.data.section_permissions || []
    const systemGroups = r.data.system_groups || []
    // TODO: remove roles check after OrgRole migration is complete (access.md §4)
    const isAdmin = systemGroups.includes('administrators') || roles.some(r => r === 'admin' || r === 'system_admin')
    // admin/system_admin always pass
    if (isAdmin) return next()
    if (requiredObject) {
      const allowed = objPerms[requiredObject] || []
      if (!allowed.includes(requiredAction) && !allowed.includes('manage')) return next('/login')
    }
    if (requiredRole === 'admin' && !isAdmin) return next('/login')
    if (requiredSection && !sections.includes(requiredSection)) return next('/login')
    if (proOnly && roles.length === 0) return next('/login')
    next()
  } catch (e) { next('/login') }
})

export default router
