# SESSION.md — 2026-08-04

## Состояние системы

### Реализовано

**Системные права (группы + реестр объектов)**
- `core/object_registry.py` — реестр объектов в коде (24 объекта из 5 приложений)
- `core/apps.py` — авто-импорт `*/object_registry.py` + `post_migrate` sync `administrators`
- `SystemGroup` — модель групповых прав с JSON `object_permissions`
- 3 группы: `administrators` (все права), `authenticated_users` (маркер), `anonymous_users` (прозрачность)
- `SystemObjectPermission` — DRF permission class

**Организационные права (роли + разделы)**
- `SiteSection` — 17 разделов (11 новых гранулярных + 6 существующих). Старые `catalog`/`configurator` деактивированы
- `OrgSectionPermission` — DRF permission class
- `Role` (OrgRole) — `django_user` удалён, переименование в `OrgRole` pending

**1:1 Django User**
- `ProjectCustomerUser.user` — 1:1 связка с Django User
- `CustomerBackend` — аутентификация через `customer_user.user` (не `role.django_user`)
- `CustomerUserAdminView` — авто-создание Django User при создании пользователя
- `CustomerMiddleware` — подставляет `request.customer` из сессии
- Миграция 0017: `Role.django_user` удалён

**API**
- `/api/auth/me/` — возвращает `system_groups`, `object_permissions`, `section_permissions`
- `/api/admin/system-groups/` — CRUD групп
- `/api/admin/object-registry/` — реестр объектов (из кода)
- `/api/admin/site-sections/` — CRUD разделов
- `/api/admin/customers/<id>/permission-matrix/` — матрица прав организации

**Фронтенд**
- Роутер: единообразные `meta.section` / `meta.object`, `PUBLIC_SECTIONS` для анонимов
- `PermissionsPage.vue` — 3 вкладки: Разделы, Матрица прав, Группы
- Вкладка «Группы»: чекбоксы в шапке колонок (выбрать/снять для всех объектов)
- `useAuth.js` — обновлён (systemGroups, objectPermissions)
- `usePerms.js` — новый shared composable (`can()`, `canSeeSection()`, `isAdmin`)
- PA-конструкторы перенесены: `/admin/pa-constructor*` → `/configurator/pa*`
- AI-вкладка исправлена в 5 каталогах

### Не сделано

- **Role → OrgRole** — переименование модели и M2M поля
- **`brand_permissions` / `series_permissions`** на `OrgRole`
- **`nomenclature.owner`** — владелец номенклатуры
- **Замена `SectionAccessPermission` → `OrgSectionPermission`** в ViewSet'ах (алиас работает)
- **Row-level security** в ViewSet'ах (queryset filter по customer)
- **Тесты Django** — написаны но не прогоняются (слишком много миграций для test DB)

### База данных

- Организации: `Система` (id=12), `Архимед` (id=1), `Неавторизованный пользователь` (id=10)
- Пользователь `kramorov` (id=1) → организация `Система` → группа `administrators`
- SystemGroup: `administrators` (24 объекта manage), `authenticated_users`, `anonymous_users`
- SiteSection: 17 разделов

### Ключевые файлы сессии

| Файл | Статус |
|---|---|
| `access.md` | Актуален |
| `core/object_registry.py` | Новый |
| `core/permissions.py` | Новый |
| `core/apps.py` | Изменён (post_migrate sync) |
| `project_customers/models/system_group.py` | Новый |
| `project_customers/models/user.py` | Изменён (system_groups, user 1:1) |
| `project_customers/models/role.py` | Изменён (django_user удалён) |
| `project_customers/models/site_section.py` | Изменён (category) |
| `project_customers/backends.py` | Переписан (1:1) |
| `project_customers/permissions.py` | Изменён (реэкспорт) |
| `project_customers/middleware.py` | Новый |
| `project_customers/views/auth.py` | Изменён (object_permissions для superuser) |
| `project_customers/views/admin_permissions.py` | Изменён (SystemGroup + ObjectRegistry views) |
| `project_customers/views/admin_customers.py` | Изменён (авто-создание Django User) |
| `project_customers/admin/role_admin.py` | Изменён (django_user убран) |
| `frontend/src/router/index.js` | Изменён (единообразные meta, PUBLIC_SECTIONS) |
| `frontend/src/pages/admin/PermissionsPage.vue` | Изменён (вкладка Группы) |
| `frontend/src/shared/composables/usePerms.js` | Новый |
| `frontend/src/components/header/useAuth.js` | Изменён |
| `*/object_registry.py` (5 файлов) | Новые |

### Миграции

```
0013_system_group              — CreateModel SystemGroup
0014_system_group_related_name — AlterField related_name='members'
0015_split_site_sections       — Data: 11 новых SiteSection
0016_site_section_category     — AddField category + populate
0017_remove_role_django_user   — RemoveField django_user
```
