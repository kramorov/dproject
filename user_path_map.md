# user_path_map.md — карта переходов пользователя (SPA)

> Составлено 2026-10-05 по коду: `frontend/src/router/index.js`, `shared/composables/useCatalogRoute.js`,
> `shared/stores/auth.js`, `shared/composables/usePerms.js`, `pages/auth/LoginMainPage.vue`,
> каталог-миниаппы `frontend/src/apps/*/App.vue`, `access.md`.
> Уровень детализации: страницы/компоненты и переходы между ними (без отдельных карточек товара).

---

## 1. Глобальные страницы (vue-router)

| URL (ru; для en/cn — префикс `/en/`, `/cn/`) | Компонент | Что это |
|---|---|---|
| `/` | `HomePage.vue` | Главная |
| `/login`, `/register` | `auth/LoginMainPage.vue` | Вход + регистрация (две панели) |
| `/catalogs/equipment`, `/catalogs/valves`, `/catalogs/solutions` | `catalog/Catalog*Index.vue` | Индексы каталогов |
| `/catalog/limit-switch` … `/catalog/filter-regulator` | `pages/catalog/*Page.vue` | Страницы каталогов (БКВ: `LimitSwitchPage.vue` → мини-апп `apps/limit-switch-catalog/App.vue`) |
| `/cart`, `/cart/:id`, `/favorites` | `CartListPage.vue`, `CartDetailPage.vue`, `FavoritesPage.vue` | Корзины, избранное |
| `/product/:id`, `/sku/:id` | `ProductPage.vue`, `SkuProductPage.vue` | Карточка товара / SKU |
| `/selector/pa` | `PaSelectionPage.vue` | Подбор ПП (секция `selector_pa`) |
| `/configurator/*` | конструкторы (`PaConstructorPage.vue` и др., часть — `PlaceholderPage.vue`) | Конструкторы оборудования |
| `/admin/*` | `pages/admin/*Page.vue` | Администрирование (права `meta.section`/`meta.object`) |
| `/tools/*`, `/ai-assistant`, `/ai-debug` | инструменты | Утилиты, AI |

**Шапка (Header.vue):** логотип → `/`; «Избранное» → `/favorites`; дропдаун корзин → `/cart/:id`;
«Вход» → `/login` (если аноним); переключатель локали → тот же путь с префиксом локали
(`localizedPath(stripLocalePrefix(route.path), target)` — состояние каталога сохраняется).

---

## 2. Авторизация: что происходит после входа

1. Пользователь попадает на страницу с `meta.section` или `meta.object/action`.
2. Гард №2 (`router.beforeEach`, асинхронный) вызывает `ensurePerms()` → один запрос `/api/auth/me/`
   (идемпотентный, кэш в `stores/auth.js`).
3. Если прав нет → `next({ path: '/login', query: { next: <полный путь> } })`.
4. `LoginMainPage.vue` → `store.login({login, password})` → `POST /api/auth/login/`
   (бэкенд: `CustomerBackend` — пароль на 1:1 Django `User`, фикс 2026-10-05).
5. После успеха: `applyProfile(response)` + `loaded=true`, затем `router.push(next || '/')`.
   **Т.е. пользователь возвращается ровно туда, откуда его отправили на логин** (`?next=`).
6. Повторный визит на защищённую страницу — гард видит `loaded=true` и не перезапрашивает.
7. **Логаут** (`Header.vue` → `store.logout()`): `POST /api/auth/logout/` → `resetAuth()` →
   `ensureAuth()` (права становятся анонимными). Редиректа нет — текущая страница остаётся;
   гард сработает при следующей навигации.
8. **Аноним**: `/auth/me/` возвращает права группы `anonymous_users` (открытые каталоги,
   конструкторы). Поэтому каталоги и подборы открываются без логина; на `/login` анонима
   отправляет только защищённая секция/объект.

Нужно изменить логику работы. Если нет прав - не нужно переходить на страницу логина. Должна отображаться обычная информация с доступом анонимным.
Если права есть - отображается информация для соответствующих прав.

---

## 3. Каталог (пример БКВ) — конечный автомат

Состояние страницы **живёт в URL**: SPA — query `?mode=&ml=&item=&from=`, standalone/embed —
`location.hash`. Компонент определяется по состоянию (`useCatalogRoute.js`):

```
item есть                → CatalogDetail        (mode=<откуда>&ml=<id>&item=<id>&from=<режим>)
ml есть, item нет        → CatalogModelLine     (mode=section&ml=<id>)  — айтемы серии
иначе mode:
  section      → CatalogSection      — сетка серий
  engineer     → EngineerSelection   — инженерный подбор (список+фильтры)
  quickselect  → QuickSelect         — быстрый подбор (чипсы)
  wizard/graph → WizardSelection / QuestionGraphWizard — мастер подбора
  ai           → AiSelectionPage     — AI подбор
```

**Переходы** (все — `router.push`, т.е. новые записи истории):

- `CatalogSection` → клик по серии → `CatalogModelLine` (brand)
- `CatalogModelLine` / `EngineerSelection` / `QuickSelect` / `Wizard` / `AI` → выбор айтема →
  `CatalogDetail` с `from=<режим>` (для бредкрамбов и кнопки «назад»)
- `CatalogDetail` → «закрыть» (`closeDetail`) → возврат в режим `from` (обычно список серии)
- Вкладки `CatalogActions` (Серии/Инженерный/Быстрый/Мастер/AI) → смена `mode` → соответствующий
  компонент; `ml/item/from` при этом сбрасываются
- `Breadcrumbs.vue` → переход на индекс каталогов или на секцию

---

## 4. Кнопка «назад» (браузер) и «закрыть» деталки

- **Каждый переход каталога — отдельная запись истории** (пуш query-параметров), поэтому
  браузерный «назад» воспроизводит предыдущее состояние: detail → список серии → секция →
  индекс каталогов. Deep-link на любое состояние работает напрямую.
- `closeDetail` — тоже пуш (снятие `item`), поэтому «вперёд» после закрытия вернёт деталку.
- `watch(page)` сбрасывает подзаголовок при уходе с brand/detail (в т.ч. по «назад»).
- **Нюанс после логина**: `router.push(next)` добавляет запись — «назад» с целевой страницы
  вернёт на `/login` (форма входа). Повторный вход/переход не зацикливается (у `/login`
  нет `meta.section/object` — гард пропускает).
- Локаль: префикс `/en/`, `/cn/` — часть маршрута; переключение локали сохраняет текущее
  состояние каталога (перенос query на локализованный путь).

---

## 5. Права доступа и переходы

- **Источник прав**: `/api/auth/me/` → `object_permissions`, `section_permissions`,
  `system_groups`. Обновляется после логина/логаута; для анонима — группа `anonymous_users`.
- **Гард №2** (`router/index.js`, перед каждым переходом):
  - `system_groups ⊇ administrators` → пропуск;
  - `meta.object` → нужен `action` (или `manage`) в `object_permissions[codename]`;
  - `meta.section` → код секции в `section_permissions`;
  - нет прав → `/login?next=<путь>`.
- **Кто что видит**:
  - аноним — открытые каталоги/конструкторы (`anonymous_users`);
  - клиентский пользователь — `system_groups` (системные) + `org_roles`/индивидуальные
    секции, с потолком прав организации (`customer.visible_sections`);
  - администратор — всё (`administrators`).
- **UI-уровень**: кнопки/вкладки скрываются/блокируются через `can('codename','action')`
  и `canSeeSection(code)` из `usePerms()` (тот же store, что и гард — двойного запроса нет).
- **Бэкенд**: DRF `SystemObjectPermission` / `OrgSectionPermission` (анонимам — права
  `anonymous_users`); каталоги отдают `AllowAny` (видимость данных — `apply_catalog_visibility`).

---

## 6. Типовые сценарии (коротко)

1. **Аноним → каталог БКВ**: `/catalog/limit-switch` → `CatalogSection` (права `anonymous_users`
   есть) → серия → айтемы → деталка. Без логина.
2. **Аноним → защищённая админка**: гард → `/login?next=/admin/...` → вход → `router.push(next)`
   → админка открыта.
3. **Вход без next** (клик «Вход» в шапке): после логина → `/`.
4. **Назад из деталки**: браузерный «назад» → список серии (или предыдущий режим по `from`).
5. **Логаут**: права сбрасываются до анонимных; защищённые страницы при следующей навигации
   отправят на `/login`.
