# access.md — Архитектура разграничения доступа

> Спроектировано 2026-07-21. Переработано 2026-07-23.
> Реализация: Этап 1 начат 2026-07-23.

---

## Концепция

Два независимых канала доступа:

| Канал | Аутентификация | Для чего | Модель прав |
|---|---|---|---|
| **API-ключ** | Заголовок `X-Api-Key` | Мини-аппы на сайтах клиентов, LLM-агент | `CustomerApiKey` → `AllowedApp` + brand filter |
| **Логин/пароль** | Django-сессия | Пользователи сайта | `ProjectCustomerUser` → `Role` → `SiteSection` |

Общее правило: **права пользователя ≤ права организации**. Организация задаёт потолок, пользователь/ключ — сужение.

---

## Обзор моделей

### Существующие (не изменяются)

```
ProjectCustomer          — организация-клиент (name, is_active, access_until, ...)
  ├── LegalEntity (1:N)  — юр. лица (ИНН, КПП, банк, ...)
  ├── CustomerSettings   — нумерация заявок, Bitrix/1C, валюта каталога
  └── ProjectCustomerUser (1:N) — пользователь (логин/пароль)
        ├── UserSettings — подпись, уведомления
        └── UserParameter — key-value параметры

clients.Company          — конечные заказчики (НЕ трогаем, другой слой)
clients.CompanyPerson    — сотрудники конечных заказчиков
producers.Brands         — бренды оборудования
```

### Новые модели (7 штук)

| № | Модель | Назначение | Этап |
|---|---|---|---|
| 1 | `SiteSection` | Справочник разделов сайта | 1 |
| 2 | `AllowedApp` | Справочник типов мини-приложений (API) | 1 |
| 3 | `Role` | Настраиваемая роль (M2M → SiteSection) | 3 |
| 4 | `CustomerAppAccess` | Org-level: доступ к мини-приложениям + brand filter | 2 |
| 5 | `CustomerEmail` | Адреса для уведомлений (заявки, счета, ...) | 2 |
| 6 | `CustomerApiKey` | API-ключи для мини-приложений | 5 |
| 7 | `FavoriteBrand` | Любимые бренды пользователя + приоритет | 4 |

### Изменяемые модели

| Модель | Изменение | Этап |
|---|---|---|
| `ProjectCustomerUser` | Убрать `role` CharField, добавить `roles` M2M → Role, `section_permissions` M2M → SiteSection, `favorite_brands` M2M → Brands (through FavoriteBrand) | 3, 4 |
| `ProjectCustomer` | Добавить M2M → SiteSection (видимые разделы), M2M → Brands (видимые бренды) | 2 |

### Будущее (спроектировано, не реализуется сейчас)

| № | Модель | Назначение |
|---|---|---|
| — | `AccessLimit` | Лимиты: access_until, max_api_calls, max_concurrent_sessions, max_sessions_per_user, max_tokens, max_disk_mb. GenericForeignKey (Customer / User). |
| — | `ApiAccessLog` | Лог API-запросов (method, path, status, response_time_ms, IP) |
| — | `UserActivityLog` | Лог действий пользователей сайта (login, view_page, search, ...) |

---

## Модель 1: `SiteSection` — разделы сайта

```python
class SiteSection(models.Model):
    """Раздел сайта, доступный пользователям."""
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    sorting_order = models.IntegerField(default=0)
```

**Значения** (фикстуры):
- `catalog` — Каталог оборудования
- `configurator` — Конфигуратор
- `requests` — Запросы клиентов
- `certificates` — Сертификаты
- `llm_agent` — Агент LLM (через сайт)

---

## Модель 2: `AllowedApp` — типы мини-приложений (API)

```python
class AllowedApp(models.Model):
    """Тип мини-приложения для API-доступа (виджеты на сайтах клиентов)."""
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    has_brand_filter = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    sorting_order = models.IntegerField(default=0)
```

**Значения** (фикстуры):

| code | name | has_brand_filter |
|---|---|---|
| `limit_switch` | Блоки концевых выключателей | true |
| `gearbox` | Ручные дублёры | true |
| `filter_regulator` | Фильтр-регуляторы | true |
| `pneumatic_fittings` | Пневмофитинги | true |
| `solenoid_valves` | Распределительные клапаны | true |
| `pa_actuators` | Пневмоприводы | true |
| `ea_actuators` | Электроприводы | true |
| `llm_agent` | LLM-агент | **false** |

`has_brand_filter = false` для `llm_agent` означает, что фильтр по брендам не применяется.

---

## Модель 3: `Role` — настраиваемая роль

```python
class Role(models.Model):
    """Роль пользователя — настраивается администратором клиента."""
    customer = models.ForeignKey(ProjectCustomer, on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    section_permissions = models.ManyToManyField(SiteSection, blank=True)
    is_default = models.BooleanField(default=False)
    sorting_order = models.IntegerField(default=0)
```

У каждой организации — свои роли. `is_default` — роль, назначаемая новому пользователю автоматически.

---

## Модель 4: `CustomerAppAccess` — доступ к мини-приложениям (org-level)

```python
class CustomerAppAccess(models.Model):
    """Разрешение организации на мини-приложение + фильтр по брендам."""
    customer = models.ForeignKey(ProjectCustomer, on_delete=models.CASCADE, related_name='app_access')
    app = models.ForeignKey(AllowedApp, on_delete=models.CASCADE)
    brand_filter = models.CharField(
        max_length=10,
        choices=[('all', 'Все бренды'), ('selected', 'Выбранные бренды')],
        default='all'
    )
    brands = models.ManyToManyField('producers.Brands', blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [['customer', 'app']]
```

**Логика**:
- `brand_filter = "all"` — мини-приложение видит все бренды
- `brand_filter = "selected"` + `brands = [A, B]` — только указанные бренды
- Для `llm_agent` (`has_brand_filter = false`) поле `brands` не используется

---

## Модель 5: `CustomerEmail` — адреса для уведомлений

```python
class CustomerEmail(models.Model):
    """Email-адреса организации для разных типов уведомлений."""
    customer = models.ForeignKey(ProjectCustomer, on_delete=models.CASCADE, related_name='notification_emails')
    email_type = models.CharField(max_length=30, choices=[
        ('requests', 'Заявки'),
        ('invoices', 'Счета'),
        ('support', 'Техподдержка'),
    ])
    email = models.EmailField()
    is_active = models.BooleanField(default=True)
```

---

## Модель 6: `CustomerApiKey` — API-ключи

```python
class CustomerApiKey(models.Model):
    """API-ключ для доступа к мини-приложениям."""
    customer = models.ForeignKey(ProjectCustomer, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=100)
    key_hash = models.CharField(max_length=128)       # SHA-256(raw_key)
    key_prefix = models.CharField(max_length=12)       # "proj_live_"

    allowed_apps = models.ManyToManyField(AllowedApp, blank=True)
    # Дополнительный фильтр брендов поверх org-level:
    # {"limit_switch": [1, 3], "gearbox": "all"}
    brand_filters = models.JSONField(default=dict, blank=True)

    ip_whitelist = models.TextField(blank=True)        # "192.168.1.5, 10.0.0.0/24"
    access_until = models.DateField(null=True, blank=True)

    # Будущее: своя LLM клиента
    llm_endpoint = models.URLField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    @classmethod
    def generate_key(cls, customer, name):
        import secrets, hashlib
        raw = f"proj_live_{secrets.token_hex(16)}"
        instance = cls(
            customer=customer, name=name,
            key_prefix="proj_live_",
            key_hash=hashlib.sha256(raw.encode()).hexdigest()
        )
        instance._raw_key = raw
        instance.save()
        return instance, raw
```

---

## Модель 7: `FavoriteBrand` — любимые бренды пользователя

```python
class FavoriteBrand(models.Model):
    """Любимый бренд пользователя с приоритетом сортировки."""
    user = models.ForeignKey(ProjectCustomerUser, on_delete=models.CASCADE, related_name='favorite_brands')
    brand = models.ForeignKey('producers.Brands', on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        unique_together = [['user', 'brand']]
        ordering = ['priority', 'brand__name']
```

Подмножество от видимых брендов организации. Если у пользователя нет записей — показываются все видимые бренды организации.

---

## Изменения в существующих моделях

### `ProjectCustomer` (Этап 2)

```python
# ДОБАВИТЬ:
visible_sections = models.ManyToManyField(SiteSection, blank=True, related_name='customers')
visible_brands = models.ManyToManyField('producers.Brands', blank=True, related_name='visible_for_customers')
```

### `ProjectCustomerUser` (Этапы 3–4)

```python
# УБРАТЬ:
ROLE_ADMIN = 'admin'
ROLE_USER = 'user'
ROLE_VIEWER = 'viewer'
ROLE_CHOICES = [...]
role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_VIEWER)

# ДОБАВИТЬ:
roles = models.ManyToManyField(Role, blank=True, related_name='users')
section_permissions = models.ManyToManyField(SiteSection, blank=True, related_name='users')
favorite_brands = models.ManyToManyField('producers.Brands', through='FavoriteBrand', blank=True, related_name='favored_by_users')
```

---

## Полная схема связей

```
                         ┌─────────────────────┐
                         │   ProjectCustomer   │
                         │  + visible_sections │──M2M──┐
                         │  + visible_brands   │──M2M──│──┐
                         └──┬──────┬──────┬────┘       │  │
                            │      │      │            │  │
              ┌─────────────┘      │      └──────┐     │  │
              │ 1:N         1:N    │ 1:N         │     │  │
              ▼              ▼     ▼             ▼     │  │
   ┌──────────────┐  ┌──────────┐ ┌────────────┐       │  │
   │    Role      │  │Cust.App  │ │Cust.ApiKey │       │  │
   │  + sect_perms│  │Access    │ │+ allowed_  │       │  │
   │    M2M───────│──│─→SiteSec │ │  apps M2M──│──┐    │  │
   │              │  │+ app FK──│─│─→AllowedApp│  │    │  │
   │              │  │  Allowed │ │+ brand_    │  │    │  │
   │              │  │  App     │ │  filters   │  │    │  │
   │              │  │+ brands──│─│─→(JSON)    │  │    │  │
   │              │  │  M2M→    │ │            │  │    │  │
   │              │  │  Brands  │ │            │  │    │  │
   └──────┬───────┘  └──────────┘ └────────────┘  │    │  │
          │ M2M                                    │    │  │
          ▼                                        │    │  │
   ┌──────────────────┐                            │    │  │
   │ ProjectCustomer  │                            │    │  │
   │      User        │                            │    │  │
   │  + roles M2M     │                            │    │  │
   │  + sect_perms ───│──M2M───────────────────────┘    │  │
   │    M2M→SiteSec   │                                 │  │
   │  + fav_brands ───│──M2M (FavoriteBrand)────────────┘  │
   │    through       │                                    │
   │    FavoriteBrand │                                    │
   └──────────────────┘                                    │
                                                           │
         ┌─────────────────────────────────────────────────┘
         │              ┌──────────────────────────────────┘
         ▼              ▼
   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────┐
   │SiteSection│   │AllowedApp│   │  Brands  │   │CustomerEmail │
   │(справочник)│   │(справочник)│  │(существ.)│   │(email_type,  │
   └──────────┘   └──────────┘   └──────────┘   │ email)       │
                                                 └──────────────┘
```

---

## Правило: права пользователя ≤ права организации

```
Пользователь видит раздел X
  ⇔ X ∈ user.effective_section_permissions   (роли ∪ индивид. permissions)
    И X ∈ customer.visible_sections           (org-level потолок)

Пользователь видит бренд B
  ⇔ B ∈ user.favorite_brands (если заполнены; пусто = все видимые)
    И B ∈ customer.visible_brands

API-ключ даёт доступ к мини-приложению A с брендами [B1, B2]
  ⇔ A ∈ key.allowed_apps
    И A ∈ customer.app_access (CustomerAppAccess)
    И brand_filter из ключа ⊂ brand_filter из CustomerAppAccess
```

`effective_section_permissions` пользователя = `section_permissions` (индивидуальные) ∪ объединение `section_permissions` всех его ролей.

---

## Матрица прав (целевая)

| Действие | superuser | customer_admin (роль) | customer_user (роль) | API-ключ |
|---|---|---|---|---|
| Django admin `/admin/` | ✅ | ✗ | ✗ | ✗ |
| Создать/управлять Customer | ✅ | ✗ | ✗ | ✗ |
| Управлять пользователями своего Customer | ✅ | +site section | ✗ | ✗ |
| Управлять API-ключами своего Customer | ✅ | +site section | ✗ | ✗ |
| Смотреть каталог | ✅ | +site section | +site section | +allowed_apps |
| Смотреть цены | ✅ | +site section | +site section | +allowed_apps |
| Конфигуратор | ✅ | +site section | +site section | ✗ |
| Создавать запросы клиентов | ✅ | +site section | +site section | ✗ |
| Сертификаты | ✅ | +site section | +site section | ✗ |
| LLM-агент (сайт) | ✅ | +site section | +site section | ✗ |
| LLM-агент (API) | ✗ | ✗ | ✗ | +allowed_apps |

---

## Будущая модель: `AccessLimit`

```python
class AccessLimit(models.Model):
    """Лимиты доступа (временные и количественные)."""
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    access_until = models.DateField(null=True, blank=True)
    max_api_calls = models.IntegerField(null=True, blank=True)
    max_concurrent_sessions = models.IntegerField(null=True, blank=True)
    max_sessions_per_user = models.IntegerField(null=True, blank=True)
    max_tokens = models.BigIntegerField(null=True, blank=True)
    max_disk_mb = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
```

Одна запись на организацию = лимиты уровня организации. Одна запись на пользователя = индивидуальные лимиты. Проверка: `min(org_limit, user_limit)`.

---

## План реализации

| Этап | Содержание | Модели |
|---|---|---|
| **1** | Справочники | `SiteSection`, `AllowedApp` + миграции + фикстуры + админка |
| **2** | Org-level доступ | `CustomerAppAccess`, `CustomerEmail`, M2M `visible_sections`/`visible_brands` на `ProjectCustomer` |
| **3** | Роли | `Role` + миграция, замена `role` CharField → `roles` M2M |
| **4** | User-level | `FavoriteBrand`, `section_permissions` M2M |
| **5** | API-ключи | `CustomerApiKey` + `AccessPermission` (DRF) |
| **6** | Фронтенд | Скрытие разделов по правам, управление пользователями, API-ключи |

---

## API-ключи: генерация, хранение, передача

### Генерация

Ключ создаётся через админку или API:

```
POST /api/auth/api-keys/
{
  "name": "Виджет НТА-Пром — БКВ",
  "allowed_apps": ["limit_switch"],
  "brand_filters": {"limit_switch": [1, 2]},
  "ip_whitelist": "195.24.68.10",
  "access_until": "2027-01-01"
}
→ {
    "id": 1,
    "raw_key": "proj_live_a3f7b2c1d4e5f6a7b8c9d0e1f2a3b4c5",
    "key_prefix": "proj_live_",
    "warning": "Сохраните raw_key — он больше не будет показан."
  }
```

**`raw_key` показывается ровно один раз.** В БД хранится только `SHA-256(raw_key)`. Потерял ключ — генерируй новый.

### Передача

Ключ передаётся в заголовке `X-Api-Key` **с каждым запросом**. Это не сессия — API-ключ не истекает за время сеанса, он действует пока `is_active=True` и `access_until` не прошёл.

**Почему с каждым запросом, а не с сессией?** API-ключ предназначен для server-to-server взаимодействия. Там нет понятия «сеанс пользователя» — каждый HTTP-запрос самостоятелен.

### Где хранить ключ на стороне клиента

**Никогда не в JS-коде.** Любой посетитель сайта клиента откроет DevTools → увидит ключ → сможет использовать его.

Правильная архитектура:

```
Браузер → сайт клиента (фронтенд)
              ↓ fetch('/wp-json/my-plugin/v1/catalog')
         сервер клиента (WordPress / PHP / Python / Node)
              ↓ curl + X-Api-Key
         наш API (Django)
```

Клиент хранит ключ в `.env` или `wp-config.php` на своём сервере. Его бэкенд проксирует запросы к нашему API, добавляя `X-Api-Key`. Браузер ключа **не видит**.

### Защита

| Механизм | Где | Назначение |
|---|---|---|
| `ip_whitelist` | `CustomerApiKey` | Принимать запросы только с IP сервера клиента |
| `access_until` | `CustomerApiKey` | Автоматическая деактивация после даты |
| `brand_filters` | `CustomerApiKey` | Сужение видимых брендов (поверх org-level) |
| `allowed_apps` | `CustomerApiKey` | Только указанные типы мини-приложений |
| `CustomerAppAccess` | Org-level | Потолок: ключ не может расширить доступ организации |

---

## WordPress: хранение ключа и прокси-запросы

### Шаг 1: Сохранить ключ в WordPress

Ключ **не должен** быть в коде плагина или темы. Три варианта хранения:

#### Вариант A: `wp-config.php` (рекомендуемый)

```php
// wp-config.php — в корне сайта, НЕ в репозитории
define('ARCHIMED_API_KEY', 'proj_live_a3f7b2c1d4e5f6a7b8c9d0e1f2a3b4c5');
define('ARCHIMED_API_URL', 'https://наш-сервер.ru/api/widget/');
```

Плюс: не потеряется при обновлении плагина/темы. Минус: нужен доступ к FTP.

#### Вариант B: Через админку WordPress (плагин)

Создать страницу настроек в админке, где клиент вставляет ключ:

```php
// В плагине: регистрируем настройку
add_action('admin_menu', function () {
    add_options_page('API Архимед', 'API Архимед', 'manage_options', 'archimed-api', 'archimed_api_page');
});

function archimed_api_page() {
    if (isset($_POST['api_key'])) {
        update_option('archimed_api_key', sanitize_text_field($_POST['api_key']));
        echo '<div class="notice notice-success"><p>Ключ сохранён</p></div>';
    }
    $key = get_option('archimed_api_key', '');
    echo '<div class="wrap">
        <h1>API Архимед</h1>
        <form method="post">
            <input type="password" name="api_key" value="' . esc_attr($key) . '"
                   placeholder="proj_live_..." style="width:400px" />
            <p class="submit"><button class="button-primary">Сохранить</button></p>
        </form>
    </div>';
}
```

Плюс: не нужен FTP. Минус: хранится в БД WordPress (сериализованные опции).

#### Вариант C: Константа в отдельном файле

```php
// wp-content/api-config.php — загружается в wp-config.php
// (можно положить ВЫШЕ public_html — недоступен из браузера)
define('ARCHIMED_API_KEY', 'proj_live_a3f7b2c1...');
```

```php
// в wp-config.php:
if (file_exists(dirname(ABSPATH) . '/api-config.php')) {
    require_once dirname(ABSPATH) . '/api-config.php';
}
```

Плюс: самый безопасный — файл вне document root. Минус: нужен FTP.

### Шаг 2: WordPress-эндпоинт для прокси

Создаём REST API endpoint в WordPress, который принимает запросы от фронтенда и проксирует их на наш сервер:

```php
// В плагине или functions.php
add_action('rest_api_init', function () {
    register_rest_route('archimed/v1', '/catalog/(?P<app>[a-z_]+)', [
        'methods'  => 'GET',
        'callback' => 'archimed_proxy_catalog',
        'permission_callback' => '__return_true', // или проверка авторизации WP
    ]);
});

function archimed_proxy_catalog(WP_REST_Request $request) {
    $app  = $request->get_param('app');      // limit_switch, gearbox, ...
    $key  = ARCHIMED_API_KEY;
    $url  = ARCHIMED_API_URL . $app . '/';

    // Прокидываем query-параметры от фронтенда
    $params = $request->get_params();
    unset($params['app']);
    if ($params) {
        $url .= '?' . http_build_query($params);
    }

    $response = wp_remote_get($url, [
        'headers' => ['X-Api-Key' => $key],
        'timeout' => 15,
    ]);

    if (is_wp_error($response)) {
        return new WP_REST_Response(['error' => 'Сервис временно недоступен'], 502);
    }

    $body = wp_remote_retrieve_body($response);
    $code = wp_remote_retrieve_response_code($response);

    return new WP_REST_Response(json_decode($body, true), $code);
}
```

### Шаг 3: Фронтенд на сайте клиента

JavaScript на странице WordPress обращается к **своему** эндпоинту, а не к нашему API напрямую:

```javascript
// На сайте клиента (WordPress)
fetch('/wp-json/archimed/v1/catalog/limit_switch?brand_id=1')
    .then(res => res.json())
    .then(data => {
        // рендерим каталог
    });
```

Поток запроса:
```
Браузер → /wp-json/archimed/v1/catalog/limit_switch?brand_id=1
             ↓ (WordPress PHP, добавляет X-Api-Key)
         GET https://наш-сервер.ru/api/widget/limit_switch/?brand_id=1
             Header: X-Api-Key: proj_live_a3f7b2c1...
             ↓
         Django AccessPermission → проверка → фильтрация → JSON
             ↓
         WordPress возвращает JSON как есть
             ↓
Браузер ← JSON с данными каталога
```

### Что получает клиент (WordPress-плагин)

Готовый мини-плагин, который клиент устанавливает себе в WordPress:

```
wp-content/plugins/archimed-widget/
├── archimed-widget.php          ← главный файл, регистрирует REST-роуты
├── admin/settings.php            ← страница настроек (поле для ввода ключа)
└── public/widget-loader.js       ← JS для фронтенда (fetch к своему эндпоинту)
```

Клиенту нужно только:
1. Установить плагин
2. Вставить ключ в настройках
3. Добавить шорткод `[archimed_widget app="limit_switch"]` на страницу

Всё остальное плагин делает сам — проксирует запросы с ключом, кэширует на 5 минут (`WP_Transient`).

---

## Сценарии

### 1. Мини-апп клиента → API-ключ

```
GET /api/widget/limit-switch/?brand_id=1
Header: X-Api-Key: proj_live_a3f7b2c1...

▼ AccessPermission.has_permission()

1. key_hash = sha256(raw_key)
2. CustomerApiKey.objects.get(key_hash=..., is_active=True)
3. Проверить access_until (если задан)
4. Проверить ip_whitelist (если задан)
5. Проверить allowed_apps → 'limit_switch' в списке?
6. Проверить CustomerAppAccess: есть ли у customer доступ к 'limit_switch'?
7. request.api_key = key
8. request.customer = key.customer
9. Обновить last_used_at

▼ View.get_queryset()

10. Применить brand_filters из ключа:
    - Взять brand_filter для 'limit_switch' из key.brand_filters
    - Если "all" → использовать CustomerAppAccess.brands (org-level)
    - Если [1, 3] → filter(brand_id__in=[1, 3])
    - Взять пересечение с CustomerAppAccess.brands
```

### 2. Пользователь сайта → логин/пароль

```
POST /api/auth/login/ {username, password}

▼ LoginView.post()

1. Django authenticate(username, password)
2. ProjectCustomerUser.objects.get(user=user)
3. Проверить is_active
4. Проверить customer.is_active и customer.access_until
5. login(request, user) → Django-сессия
6. Вернуть {username, role_codes, section_permissions, customer}

▼ Фронтенд

7. Показывает только разделы из section_permissions
8. customer_admin видит страницу управления пользователями
```
