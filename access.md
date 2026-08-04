# access.md — Архитектура разграничения доступа

> Спроектировано 2026-07-21. Переработано 2026-07-23, 2026-08-04.
> Реализация: Этап 1 начат 2026-07-23. Переработка: 2026-08-04.

---

## Терминология

| Уровень | Термин | Аналог Windows | Что определяет |
|---|---|---|---|
| Системный | **Группа** (SystemGroup) | `Administrators`, `Users` | Что можно **делать** в системе |
| Организационный | **Роль** (OrgRole) | Кастомные группы в AD | Что **видно** внутри организации |

**XOR-правило:** каждый ресурс (страница, API, кнопка) защищается **либо** системной группой, **либо** организационной ролью — не обоими сразу.

---

## Концепция

Два независимых канала доступа:

| Канал | Аутентификация | Для чего | Модель прав |
|---|---|---|---|
| **API-ключ** | Заголовок `X-Api-Key` | Мини-аппы на сайтах клиентов, LLM-агент | `CustomerApiKey` → `AllowedApp` + brand filter |
| **Логин/пароль** | Django-сессия | Пользователи сайта | `ProjectCustomerUser` → `SystemGroup` (системные) + `OrgRole` → `SiteSection` (организационные) |

Общее правило: **права пользователя ≤ права организации**. Организация задаёт потолок, пользователь/ключ — сужение.

---

## Django User — оболочка аутентификации (1:1)

Каждый `ProjectCustomerUser` имеет свой персональный Django `User`.
Это контейнер для логина/пароля/сессии. **Никаких прав в Django.**

```python
class ProjectCustomerUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    # Django User используется ТОЛЬКО для:
    #   - аутентификации (login + password)
    #   - Django-сессии (request.user)
    #   - аудита (created_by = request.user)
    #
    # ПРАВА В DJANGO: is_staff=False, is_superuser=False, user_permissions=[],
    #   groups=[] (все права — через system_groups + org_roles)
```

### Права Django User

| Поле | Значение | Почему |
|---|---|---|
| `is_staff` | `False` | Не пускать в `/admin/` |
| `is_superuser` | `False` | Не давать системных прав |
| `user_permissions` | Пусто | Все разрешения через наш слой |
| `groups` | Пусто | Django groups не используются |

### Создание — автоматическое

При создании `ProjectCustomerUser` Django User создаётся автоматически:

```
POST /api/admin/customers/<id>/users/  { login: "ivanov", password: "..." }
  │
  ├─ User.objects.create_user(username=f'cust_{customer_id}_{login}', password=...)
  ├─ ProjectCustomerUser.objects.create(user=django_user, customer=..., login=...)
  └─ Возвращает: { id, login, system_groups, roles, ... }
```

### Преимущества 1:1

- `request.user` → всегда конкретный человек, не роль
- `request.user.customer_profile` → быстрый доступ к ProjectCustomerUser
- Row-level security: `MyModel.objects.filter(owner=request.user)`
- Аудит: `created_by = ForeignKey(User)` — кто реально создал запись
- Один аккаунт = одна сущность, без дублирования

---

## Системный уровень: группы и реестр объектов

### Реестр объектов (в коде, не в БД)

Файл: `core/object_registry.py`. Хранит **названия** всех защищаемых объектов. Заполняется декларативно через `register_object()`.

```python
# core/object_registry.py
OBJECT_REGISTRY = {}  # {codename: {name, type, parent}}

def register_object(*, codename, name, type, parent=None):
    OBJECT_REGISTRY[codename] = {...}
```

Каждое приложение регистрирует свои объекты в `<app>/object_registry.py`:

```python
# pneumatic_actuators/object_registry.py
from core.object_registry import register_object

register_object(codename='configurator.pa', name='Конфигуратор пневмоприводов', type='configurator')
register_object(codename='catalog.pa',       name='Каталог пневмоприводов',     type='catalog')
register_object(codename='admin.sku',        name='Управление SKU',             type='admin_page')
```

### Типы объектов

| Тип | Назначение | Пример |
|---|---|---|
| `page` | Страница (роут фронтенда) | `/admin/customers` |
| `api` | API-эндпоинт | `POST /api/admin/site-sections/` |
| `ui_element` | Кнопка/ссылка/блок | «Удалить клиента» |
| `configurator` | Конфигуратор (подтип page) | Конфигуратор ПП |
| `catalog` | Раздел каталога (подтип page) | Ручные дублёры |

### SystemGroup — группа системных прав (в БД)

```python
class SystemGroup(models.Model):
    """Именованная группа системных прав (аналог группы Windows)."""
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    object_permissions = models.JSONField(default=dict)
    # {
    #   "configurator.pa":   ["view", "edit"],
    #   "admin.customers":   ["view", "edit", "delete"],
    #   "catalog.gearbox":   ["view"],
    # }
    is_default = models.BooleanField(default=False)
    sorting_order = models.IntegerField(default=0)
```

### Действия (actions)

| Действие | Что означает |
|---|---|
| `view` | Видеть/читать |
| `edit` | Редактировать/создавать |
| `delete` | Удалять |
| `manage` | ≡ все три (`view` + `edit` + `delete`) |

### Фикстуры: системные группы

| Группа (code) | Название | Кому |
|---|---|---|
| `administrators` | Администраторы | Разработчики, все права |
| `customer_managers` | Менеджеры клиентов | Управление организациями, пользователями, ключами |
| `catalog_managers` | Редакторы каталога | SKU, цены, сертификаты |
| `media_editors` | Редакторы медиа | Медиабиблиотека |
| `ai_configurators` | AI-инженеры | Настройка pipeline, skills, отладка |
| `authenticated_users` | Авторизованные пользователи | Маркер (без прав, просто «вошёл») |

### Жизненный цикл объекта

| Событие | Поведение |
|---|---|
| Новый объект в коде | Автоматически виден в `/admin/permissions`, но прав нет ни у кого (secure by default) |
| Удалённый объект из кода | Старые права в JSON — мёртвый груз, доступ не дают |
| Переименован `codename` | Старый ключ — мусор, новый — без прав (выдавать заново) |

---

## Организационный уровень: роли и разделы

### OrgRole — роль внутри организации

> `Role.django_user` удалён. Роль больше не содержит ссылку на Django User.
> Вход — через персональный `ProjectCustomerUser.user` FK (1:1).

```python
class OrgRole(models.Model):
    """Роль внутри организации."""
    customer = models.ForeignKey(ProjectCustomer, on_delete=models.CASCADE, related_name='org_roles')
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    section_permissions = models.ManyToManyField(SiteSection, blank=True)
    is_default = models.BooleanField(default=False)
    sorting_order = models.IntegerField(default=0)
```

### SiteSection — разделы сайта (гранулярно)

**Было:** `catalog`, `configurator`, `requests`, `certificates`, `llm_agent`

**Стало (разбито):**

| code | Название | Группа |
|---|---|---|
| `catalog_gearbox` | Ручные дублёры | catalog |
| `catalog_pa` | Пневмоприводы | catalog |
| `catalog_ea` | Электроприводы | catalog |
| `catalog_lsb` | Блоки концевых выключателей | catalog |
| `catalog_sv` | Соленоидные клапаны | catalog |
| `catalog_fr` | Фильтр-регуляторы | catalog |
| `catalog_pf` | Пневмофитинги | catalog |
| `catalog_cg` | Кабельные вводы | catalog |
| `configurator_pa` | Конфигуратор ПП | configurator |
| `configurator_ea` | Конфигуратор ЭП | configurator |
| `configurator_cab` | Шкафы управления | configurator |
| `requests` | Заявки клиентов | requests |
| `certificates` | Сертификаты | certificates |
| `llm_agent` | Агент LLM | ai |

Поле `SiteSection.category` группирует разделы (для UI):

```python
class SiteSection(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, default='catalog')  # ← новое
    is_active = models.BooleanField(default=True)
    sorting_order = models.IntegerField(default=0)
```

---

## ProjectCustomerUser

```python
class ProjectCustomerUser(models.Model):
    # Django User — оболочка аутентификации (1:1, автосоздание)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')

    # СИСТЕМНЫЕ права (не зависят от организации)
    system_groups = models.ManyToManyField(SystemGroup, blank=True)

    # ОРГАНИЗАЦИОННЫЕ права (per-customer)
    customer = models.ForeignKey(ProjectCustomer, ...)
    org_roles = models.ManyToManyField(OrgRole, blank=True)              # было: roles
    section_permissions = models.ManyToManyField(SiteSection, blank=True) # индивид.

    def has_system_perm(self, codename: str, action: str = 'view') -> bool:
        """Проверить системное право на объект."""
        for group in self.system_groups.all():
            perms = group.object_permissions.get(codename, [])
            if action in perms or 'manage' in perms:
                return True
        return False

    def get_object_permissions(self) -> dict:
        """Все системные права пользователя: {codename: [actions]}."""
        result = {}
        for group in self.system_groups.all():
            for obj, actions in group.object_permissions.items():
                result.setdefault(obj, set()).update(actions)
        return {k: list(v) for k, v in result.items()}

    def get_effective_section_permissions(self):
        """Организационные права: OrgRole + индивид."""
        from project_customers.models import SiteSection
        role_sections = SiteSection.objects.filter(orgrole__users=self)
        individual = self.section_permissions.all()
        return (role_sections | individual).distinct()
```

---

## Полная схема связей

```
┌─────────────────────────────────────────────────────────────┐
│                    СИСТЕМНЫЙ УРОВЕНЬ                         │
│                                                             │
│  SystemGroup (БД)              Object Registry (код)         │
│  ├─ code: 'administrators'     core/object_registry.py      │
│  ├─ object_permissions: JSON   ├─ configurator.pa           │
│  │   {                         ├─ catalog.gearbox           │
│  │     "admin.customers":      ├─ ai.pipelines              │
│  │       ["view","edit"],      └─ ...                       │
│  │     "catalog.gearbox":                                   │
│  │       ["view"],                                         │
│  │   }                                                     │
│  └─ is_default                                              │
│       │ M2M                                                 │
│       ▼                                                     │
│  ProjectCustomerUser.system_groups                          │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                   ОРГАНИЗАЦИОННЫЙ УРОВЕНЬ                    │
│                                                             │
│  ProjectCustomer                                             │
│  ├─ visible_sections M2M → SiteSection (потолок)            │
│  └─ OrgRole (1:N)                                           │
│       ├─ section_permissions M2M → SiteSection               │
│       └─ M2M → ProjectCustomerUser.org_roles                 │
│                                                             │
│  SiteSection (справочник)                                    │
│  ├─ catalog_gearbox, catalog_pa, catalog_lsb, ...           │
│  ├─ configurator_pa, configurator_ea, configurator_cab      │
│  ├─ requests, certificates, llm_agent                       │
│  └─ category (для группировки в UI)                         │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                      ДАННЫЕ (будущее)                        │
│                                                             │
│  nomenclature.owner → FK ProjectCustomerUser                │
│  brand/series visibility → через OrgRole + потолок org       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Правило: права пользователя ≤ права организации

```
Системный доступ:
  Пользователь может выполнить действие X над объектом Y
    ⇔ Y ∈ OBJECT_REGISTRY
      И X ∈ user.get_object_permissions()[Y]

Организационный доступ:
  Пользователь видит раздел X
    ⇔ X ∈ user.effective_section_permissions   (OrgRole ∪ индивид.)
      И X ∈ customer.visible_sections           (org-level потолок)

API-ключ даёт доступ к мини-приложению A с брендами [B1, B2]
  ⇔ A ∈ key.allowed_apps
    И A ∈ customer.app_access (CustomerAppAccess)
    И brand_filter из ключа ⊂ brand_filter из CustomerAppAccess
```

---

## Многоуровневая защита данных (multi-tenant)

Ограничение на уровне организации — через фильтрацию queryset'ов по `customer_id`, не через Django-права.

### CustomerMiddleware

```python
# project_customers/middleware.py
class CustomerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        profile_id = request.session.get('customer_user_id')
        if profile_id:
            try:
                profile = ProjectCustomerUser.objects.select_related('customer').get(
                    id=profile_id, is_active=True
                )
                request.customer_user = profile
                request.customer = profile.customer
            except ProjectCustomerUser.DoesNotExist:
                pass
        return self.get_response(request)
```

### Три слоя защиты

| Слой | Где | Что фильтрует |
|---|---|---|
| **View** | `ViewSet.get_queryset()` | `filter(customer=request.customer)` |
| **Middleware** | `CustomerMiddleware` | Подставляет `request.customer` из сессии |
| **API-ключ** | `AccessPermission` | Уже подставляет `request.customer = api_key.customer` |

---

## Проверки на каждом слое

### Бэкенд: DRF permission classes

```python
# core/permissions.py

class SystemObjectPermission(BasePermission):
    """Проверка системного права через реестр объектов."""
    def has_permission(self, request, view):
        obj = getattr(view, 'required_object', None)
        action = getattr(view, 'required_action', 'view')
        if obj is None:
            return True
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        profile = get_customer_profile(request)
        if not profile:
            return False
        return profile.has_system_perm(obj, action)


class OrgSectionPermission(BasePermission):
    """Проверка организационного доступа через SiteSection."""
    def has_permission(self, request, view):
        if getattr(view, 'public', False):
            return True
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True

        required_section = getattr(view, 'required_section', None)
        if required_section is None:
            return True

        from project_customers.utils import get_customer_profile
        profile = get_customer_profile(request)
        if profile is None:
            return False

        effective = profile.get_effective_section_permissions()
        return effective.filter(code=required_section).exists()
```

### Фронтенд: роутер

```javascript
// XOR: каждый маршрут задаёт ЛИБО object, ЛИБО section
{ path: '/admin/customers',    meta: { object: 'admin.customers',   action: 'view' } }
{ path: '/admin/permissions',  meta: { object: 'admin.permissions', action: 'edit' } }
{ path: '/configurator/pa',    meta: { object: 'configurator.pa',   action: 'view' } }
{ path: '/catalog/gearbox',    meta: { section: 'catalog_gearbox' } }

router.beforeEach(async (to, from, next) => {
  const required = to.meta.object || to.meta.section
  if (!required) return next()

  const r = await api.get('/auth/me/')
  const perms = r.data.object_permissions || {}
  const sections = r.data.section_permissions || []

  // Системная проверка: object + action
  if (to.meta.object) {
    const allowed = perms[to.meta.object] || []
    if (!allowed.includes(to.meta.action || 'view')) return next('/login')
  }

  // Организационная проверка: section
  if (to.meta.section && !sections.includes(to.meta.section)) return next('/login')

  next()
})
```

### Фронтенд: условный рендеринг

```javascript
// composable usePerms.js
const { can } = usePerms()

<NavLink v-if="can('admin.customers', 'view')"    to="/admin/customers">Клиенты</NavLink>
<EditButton v-if="can('configurator.pa', 'edit')"  @click="save" />
<DeleteButton v-if="can('admin.customers', 'delete')" />

// Стили:
<div :class="{ readonly: !can('configurator.pa', 'edit') }">
  <input :disabled="!can('configurator.pa', 'edit')" />
</div>
```

### `/auth/me/` — формат ответа

```json
{
  "username": "Иванов Иван",
  "email": "i.ivanov@romashka.ru",
  "system_groups": ["customer_managers"],
  "object_permissions": {
    "admin.customers":     ["view", "edit"],
    "admin.permissions":   ["view"],
    "catalog.gearbox":    ["view"]
  },
  "org_roles": ["engineer"],
  "section_permissions": ["catalog_gearbox", "catalog_pa", "configurator_pa"],
  "customer": "ООО Ромашка"
}
```

---

## Реализовано (существующее, не меняется)

Модели: `CustomerApiKey`, `AllowedApp`, `CustomerAppAccess`, `CustomerEmail`, `FavoriteBrand`

API-ключи: генерация, хранение (SHA-256), передача (`X-Api-Key`), WordPress-прокси.

`core/access.py`: `catalog_permission_classes()` + `apply_catalog_visibility()` — заглушки `AllowAny`.

---

## Этапы реализации (пересмотрено 2026-08-04)

| Этап | Содержание | Модели/файлы |
|---|---|---|
| **1** | Реестр объектов ✓ | `core/object_registry.py`, `<app>/object_registry.py` |
| **2** | SystemGroup + миграция ✓ | `SystemGroup`, `ProjectCustomerUser.system_groups` |
| **3** | Разбивка SiteSection ✓ | 11 новых разделов, 2 деактивированы |
| **4** | 1:1 Django User ✓ | Миграция 0017, `CustomerBackend`, `CustomerMiddleware` |
| **5** | DRF permission classes ✓ | `SystemObjectPermission`, `OrgSectionPermission` |
| **6** | `/auth/me/` + Permissions UI ✓ | `CurrentUserView`, `PermissionsPage.vue` |
| **7** | Фронтенд: роутер + usePerms ✓ | `router/index.js`, `useAuth.js`, `usePerms.js` |
| **8** | Auto-sync админа ✓ | `core/apps.py` → `post_migrate`, все объекты → `manage` |
| **9** | API-ключи (без изменений) | `CustomerApiKey` + `AccessPermission` (DRF) |
| **10** | Role → OrgRole | Переименование модели, `org_roles` M2M |

### На будущее

- `brand_permissions`, `series_permissions` на `OrgRole`
- `nomenclature.owner` — владелец номенклатуры
- `AccessLimit` — лимиты (access_until, max_api_calls, ...)
- `ApiAccessLog` / `UserActivityLog` — логирование
