# access.md — Архитектура разграничения доступа

> Спроектировано 2026-07-21. Реализация — следующий этап.

---

## Концепция

Два независимых механизма доступа:

| Механизм | Для чего | Как работает |
|---|---|---|
| **API-ключ** | Мини-аппы на сайтах клиентов | Заголовок `X-Api-Key` → доступ к API, фильтры контента |
| **Логин/пароль** | Пользователи сайта | Django-сессия → разделы сайта по permissions |

---

## Модели

```python
# === ProjectCustomer (добавить) ===
class ProjectCustomer(models.Model):
    # существующие поля: name, is_active, access_until, ...
    pass
    # api-ключи — через related_name='api_keys' от CustomerApiKey


# === НОВАЯ: CustomerApiKey ===
class CustomerApiKey(models.Model):
    """API-ключ для мини-аппов на сайтах клиентов."""
    customer = models.ForeignKey(ProjectCustomer, related_name='api_keys')
    name = models.CharField("Название", max_length=100)
    key_hash = models.CharField(max_length=128)          # SHA-256(raw_key)
    key_prefix = models.CharField(max_length=12)          # "proj_live_"

    # Какие мини-приложения доступны
    allowed_apps = models.ManyToManyField('AllowedApp')

    # Фильтры контента: {"brand_ids": [1,3], "series_ids": [2]}
    content_filters = models.JSONField(default=dict, blank=True)

    # IP-whitelist (пусто = без ограничений), "192.168.1.5, 10.0.0.0/24"
    ip_whitelist = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True)

    def save(self, *args, **kwargs):
        if not self.key_hash and hasattr(self, '_raw_key'):
            self.key_hash = hashlib.sha256(self._raw_key.encode()).hexdigest()
        super().save(*args, **kwargs)

    @classmethod
    def generate_key(cls, customer, name):
        """Генерирует ключ, возвращает (instance, raw_key)."""
        raw = f"proj_live_{secrets.token_hex(16)}"
        instance = cls(customer=customer, name=name, key_prefix="proj_live_")
        instance._raw_key = raw
        instance.save()
        return instance, raw


# === НОВАЯ: AllowedApp ===
class AllowedApp(models.Model):
    """Типы мини-приложений."""
    APP_CHOICES = [
        ('limit_switch',       'Блоки концевых выключателей'),
        ('gearbox',            'Ручные дублёры'),
        ('filter_regulator',   'Фильтр-регуляторы'),
        ('pneumatic_fittings', 'Пневмофитинги'),
        ('solenoid_valves',    'Распределительные клапаны'),
        ('pa_actuators',       'Пневмоприводы'),
        ('ea_actuators',       'Электроприводы'),
    ]
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)


# === НОВАЯ: SectionPermission ===
class SectionPermission(models.Model):
    """Разделы сайта."""
    SECTION_CHOICES = [
        ('catalog',       'Каталог оборудования'),
        ('prices',        'Цены и прайс-листы'),
        ('constructor',   'Конфигуратор'),
        ('requests',      'Запросы клиентов'),
        ('certificates',  'Сертификаты'),
    ]
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)


# === ProjectCustomerUser (изменить) ===
class ProjectCustomerUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    customer = models.ForeignKey(ProjectCustomer, on_delete=models.CASCADE)

    ROLE_CUSTOMER_ADMIN = 'customer_admin'
    ROLE_CUSTOMER_USER  = 'customer_user'

    role = models.CharField(choices=[
        (ROLE_CUSTOMER_ADMIN, 'Администратор клиента'),
        (ROLE_CUSTOMER_USER,  'Пользователь клиента'),
    ], default=ROLE_CUSTOMER_USER)

    section_permissions = models.ManyToManyField(SectionPermission, blank=True)

    # ... существующие поля (first_name, last_name, email, phone, position, ...)


# === НОВАЯ: ApiAccessLog ===
class ApiAccessLog(models.Model):
    """Лог запросов через API-ключи (мини-аппы)."""
    api_key = models.ForeignKey(CustomerApiKey, on_delete=models.SET_NULL, null=True)
    customer = models.ForeignKey(ProjectCustomer, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=500)
    query_params = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField()
    response_status = models.IntegerField()
    response_time_ms = models.IntegerField()


# === НОВАЯ: UserActivityLog ===
class UserActivityLog(models.Model):
    """Лог действий пользователей сайта."""
    user = models.ForeignKey(ProjectCustomerUser, on_delete=models.SET_NULL, null=True)
    customer = models.ForeignKey(ProjectCustomer, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=50)  # login, logout, view_page, search, api_request
    path = models.CharField(max_length=500, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField()
```

---

## Сценарии

### 1. Мини-апп клиента → API-ключ

```
GET /api/widget/limit-switch/?brand_id=1
Header: X-Api-Key: proj_live_a3f7b2c1...

▼ AccessPermission.has_permission()

1. key_hash = sha256(raw_key)
2. CustomerApiKey.objects.get(key_hash=key_hash)
3. Проверить is_active
4. Проверить ip_whitelist (если задан)
5. Проверить allowed_apps → 'limit_switch' в списке?
6. request.api_key = найденный ключ
7. request.customer = api_key.customer
8. Обновить last_used_at

▼ View.get_queryset()

9. Применить content_filters:
   если brand_ids заданы → filter(brand_id__in=...)
   если series_ids заданы → filter(series_id__in=...)

▼ Middleware (response)

10. Записать ApiAccessLog (метод, путь, статус, время ответа, IP)
```

### 2. Пользователь сайта → логин/пароль

```
POST /api/auth/login/ {username, password}

▼ LoginView.post()

1. Django authenticate(username, password)
2. ProjectCustomerUser.objects.get(user=user)
3. login(request, user)  → Django-сессия
4. Вернуть {role, section_permissions, customer}

▼ UserActivityLog (middleware)

5. Записать: action='login', user, customer, ip

▼ Фронтенд

6. Показывает только разделы из section_permissions
7. customer_admin видит страницу управления пользователями
```

---

## Права: кто что может

| Действие | superuser | customer_admin | customer_user | API-ключ |
|---|---|---|---|---|
| Django admin `/admin/` | ✅ | ✗ | ✗ | ✗ |
| Создать ProjectCustomer | ✅ | ✗ | ✗ | ✗ |
| Создать CustomerApiKey | ✅ | ✗ | ✗ | ✗ |
| Управлять пользователями своего Customer | ✅ | ✅ | ✗ | ✗ |
| Смотреть каталог | ✅ | +permissions | +permissions | +allowed_apps |
| Смотреть цены | ✅ | +permissions | +permissions | +allowed_apps |
| Создавать запросы клиентов | ✅ | +permissions | +permissions | ✗ |
| Доступ к API (мини-аппы) | ✗ | ✗ | ✗ | ✅ |

---

## План реализации

### Этап 1: Модели и миграции
- [ ] `AllowedApp` — модель + миграция + фикстуры (7 типов)
- [ ] `SectionPermission` — модель + миграция + фикстуры (5 разделов)
- [ ] `CustomerApiKey` — модель + миграция
- [ ] `ProjectCustomerUser` — замена `role` + `section_permissions` M2M + миграция
- [ ] `ApiAccessLog` — модель + миграция
- [ ] `UserActivityLog` — модель + миграция

### Этап 2: Permission class + Middleware
- [ ] `core/permissions.py` — `AccessPermission` (DRF BasePermission)
- [ ] `core/middleware.py` — `AccessLogMiddleware` (логирование API-запросов)
- [ ] `core/middleware.py` — `UserActivityMiddleware` (логирование действий пользователей)

### Этап 3: Интеграция
- [ ] `core/views.py` — `UniversalAPIView`: добавить `permission_classes = [AccessPermission]`
- [ ] `core/views.py` — `BaseCatalogView`: фильтрация по `request.customer` / `request.api_key.content_filters`
- [ ] `clients/models.py` — `Company.get_for_user`: использовать `request.customer` вместо streamlit-сессии
- [ ] `project_customers/views/auth.py` — `LoginView`: вернуть `section_permissions`
- [ ] `project_customers/views/auth.py` — `CurrentUserView`: вернуть `section_permissions`

### Этап 4: Админка
- [ ] Django admin для `CustomerApiKey` (с генерацией ключа)
- [ ] Django admin для `ProjectCustomerUser` (назначение section_permissions)
- [ ] Дашборд логов в админке

### Этап 5: Фронтенд
- [ ] `router/index.js` — скрывать разделы по `section_permissions`
- [ ] Страница управления пользователями для `customer_admin`
- [ ] Страница «Мои API-ключи»
