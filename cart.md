# cart.md — Корзина и Избранное

> Дата: 2026-08-10. Приложение: `cart`. Бэкенд: Django REST. Фронт: Vue 3.

---

## Назначение

Универсальная корзина для B2B-подбора оборудования. Пользователь собирает товары из каталогов в корзину, изменяет количество, просматривает деталировку, оформляет заказ. Поддерживает анонимных пользователей (сессия), авторизованных (БД), избранное, несколько корзин.

---

## Модели

### Cart (cart/models/cart.py)

```python
id: UUIDField                       # первичный ключ
cart_type: CharField                # 'cart' / 'favorites'
name: CharField(max_length=200)     # название (для идентификации)
description: TextField              # описание (ОЛ, объект, заметки)
status: CharField                   # 'active' / 'ordered' / 'abandoned'
is_active_cart: BooleanField        # указатель активной корзины (только одна на user/session)

# Владелец
user: FK(User, nullable)            # авторизованный пользователь
session_key: CharField(40)          # анонимная сессия
project_customer: FK(ProjectCustomer, nullable)
employee: FK(ProjectCustomerUser, nullable)

# Конвертация
client_request: FK(ClientRequest, nullable)  # созданная заявка

created_at / updated_at: DateTimeField
```

**Методы:**
- `set_active()` — деактивирует все остальные корзины пользователя, активирует эту
- `get_active(user, session_key)` — возвращает активную (is_active_cart=True) или последнюю
- `has_any(user, session_key)` — есть ли хоть одна активная корзина

### CartItem (cart/models/cart_item.py)

```python
id: UUIDField
cart: FK(Cart, CASCADE, related_name='items')
sku: FK(SKU, PROTECT)               # связь с номенклатурой (НЕ с моделью напрямую)
quantity: PositiveIntegerField

# Кеш цены (обновляется раз в день)
price_snapshot: DecimalField        # цена в RUB на дату price_date
price_date: DateField               # если < сегодня → пересчёт через ExchangeRate
price_currency: CharField(3)        # всегда RUB после конвертации

added_at: DateTimeField
notes: TextField
```

**Методы:**
- `get_equipment_summary()` — артикул, название, бренд, фото, характеристики, source-ссылка

### CartEvent (cart/models/cart_event.py)

```python
id: UUIDField
cart: FK(Cart, CASCADE, related_name='events')
event_type: CharField               # created / item_added / item_removed / item_qty / renamed / ordered / abandoned
data: JSONField                     # item_id, quantity, old_name, new_name...
created_at: DateTimeField
```

**Класс-метод:**
- `CartEvent.log(cart, event_type, **data)` — утилита для записи события

---

## API

| Метод | Путь | Описание | Логирование |
|---|---|---|---|
| `GET` | `/api/cart/` | Список корзин пользователя (CartBare) | — |
| `GET` | `/api/cart/active/` | Активная корзина с позициями (Cart) | — |
| `GET` | `/api/cart/{id}/` | Конкретная корзина с позициями | — |
| `GET` | `/api/cart/favorites/` | Избранное | — |
| `POST` | `/api/cart/add/` | Добавить SKU в корзину | ITEM_ADDED / ITEM_QTY |
| `POST` | `/api/cart/create/` | Создать новую корзину (авто-активная) | CREATED |
| `POST` | `/api/cart/{id}/activate/` | Сделать корзину активной | activated |
| `POST` | `/api/cart/checkout/` | Оформить заказ (заглушка → ordered) | ORDERED |
| `PATCH` | `/api/cart/{id}/manage/` | Переименовать / сменить статус | RENAMED |
| `DELETE` | `/api/cart/{id}/manage/` | Удалить (soft → abandoned) | ABANDONED |
| `DELETE` | `/api/cart/items/{id}/` | Удалить позицию | ITEM_REMOVED |
| `PATCH` | `/api/cart/items/{id}/update/` | Изменить количество / заметки | ITEM_QTY / ITEM_REMOVED |
| `GET` | `/api/cart/items/{id}/detail/` | Деталировка товара (прокси к каталогу) | — |

### Прокси к каталогу

`GET /api/cart/items/{id}/detail/` резолвит:
```
CartItem.sku → SKU.source_object (GFK) → app_label → catalog API prefix
→ http://127.0.0.1:8000/api/{prefix}/catalog/{pk}/
→ возвращает данные в формате ProductDetail
```

Маппинг `app_label → API prefix` — константа `_CATALOG_API_MAP` в `cart/views.py`.

---

## Цена

Логика в `_resolve_sku_price(sku_id, existing_item)` (`cart/serializers.py`):

1. Если `existing_item.price_date >= today` → вернуть кеш из `price_snapshot`
2. Иначе → `PriceHistory.get_current_price_by_sku(sku_id, price_variety)`
3. Если валюта ≠ RUB → конвертация через `ExchangeRate`: `price × rate / nominal`
4. Кешировать результат в `CartItem.price_snapshot` с `price_date=today`, `price_currency=RUB`
5. Вернуть `{price: rub, currency_symbol: '₽', currency_code: 'RUB'}`

**Зависимости:** `price.PriceHistory`, `price.PriceVariety`, `price.Currency`, `price.models.exchange_rate.ExchangeRate`.

---

## Активная корзина

У пользователя может быть несколько корзин, но только одна **активная** — в неё добавляются товары через API `add/`.

- Флаг `Cart.is_active_cart` — только один `True` на (user, cart_type)
- `Cart.set_active()` — атомарно деактивирует остальные, активирует эту
- `Cart.get_active()` — ищет `is_active_cart=True`, fallback на последнюю
- Новый `create_cart` — автоматически активна, старые деактивируются
- `POST /activate/` — ручная активация

---

## Анонимные пользователи

- Идентификация через `session_key` (Django-сессия)
- При логине: `merge_anonymous_cart(request, user)` переносит анонимные корзины на пользователя
- Избранное мержится с дедупликацией (quantity = max)
- Старые анонимные корзины чистятся: `python manage.py cleanup_anonymous_carts --days 30`

---

## Фронт

### Компоненты (shared)

| Компонент | Назначение |
|---|---|
| `AddToCartButton.vue` | Кнопка 🛒 + ★ на карточке товара. Глобальный кеш (1 API-запрос на все карточки). Слушает `cart-updated` |
| `EmptyState.vue` | Универсальный empty state: SVG-иконка, заголовок, текст, подитог |
| `EquipmentListView.vue` | Грид/список товаров (режим `grid`/`list`, переключатель `showModeSwitch`, слот `#controls`, адаптеры `toCardItem`/`toPrice`) |
| `ProductDetailPopup.vue` | Попап карточки товара: `GET /api/cart/items/{id}/detail/` → `ProductDetail`. Закрытие по кнопке (не по клику вне) |
| `ProgressiveImage.vue` | Прогрессивная загрузка изображений (preview → full) |

### Страницы

| Страница | URL | Описание |
|---|---|---|
| `CartListPage.vue` | `/cart` | Список корзин: металлическая карточка с именем, статусом, датой. ▶ активация, 🗑 удаление. Нет модалки редактирования — ✏️ кнопка убрана |
| `CartDetailPage.vue` | `/cart/:id` | Полноэкранный режим. **Инлайн-редактирование** name и description (сохраняются по `@blur`). `EquipmentListView` с контролами: цена, сумма, qty, удалить. `ProductDetailPopup` по клику. `watch(cartId)` для перерисовки при смене URL |
| `FavoritesPage.vue` | `/favorites` | `EquipmentListView` с контролами: цена, 🛒 перенос в корзину, 🗑 удалить. `EmptyState` при пустом списке |
| `ProductPage.vue` | `/product/:id` | Отдельная страница товара: `GET /api/cart/items/{id}/detail/` → `<ProductDetail>`. Использует `watch` с `immediate` |

### Хедер

**Корзина:**
- Клик → `/cart` (список корзин)
- Ховер → **дропдаун со списком активных корзин** (текущая — жирная + синяя, счётчик позиций)
- Внизу дропдауна — кнопка «+ Новая корзина» (создаёт и сразу открывает)
- SVG-иконка тележки + красный счётчик-бейдж

**Избранное:**
- SVG-сердечко, при наведении — краснеет
- Клик → `/favorites`
- Скачан SVG `favorites-empty.svg` в `frontend/public/`

Счётчик обновляется через `cart-updated` событие.

### Пустые состояния

- **Пустая корзина**: SVG-тележка, «В корзине пока нет товаров» / «Нажмите 🛒 на странице товара и добавляйте сюда то, что нужно»
- **Пустое избранное**: SVG из Vseinstrumenti.ru (`favorites-empty.svg` в `public/`), «В избранном пока нет товаров» / «Жмите ❤️ на странице товара и добавляйте сюда то, что нравится»

### Default'ы

- Новая корзина: `Новая корзина {YY-MM-DD-HH-MM}` (формат datetime)
- Стратегии авто-выбора чипсов в QuickSelect: `first`, `min`, `max` (из `FilterSet.defaults`)
- `description` сохраняется через `PATCH /api/cart/{id}/manage/` (добавлен в `UpdateCartSerializer`)

### Сервис

`cartService.js` — все API-вызовы. Базовый префикс `/cart` (axios добавляет `/api`). Методы: `getActive`, `getList`, `getCart`, `getFavorites`, `addItem`, `addToFavorites`, `updateItem`, `removeItem`, `createCart`, `updateCart`, `deleteCart`, `activateCart`, `getActiveCartStatus`, `getItemDetail`, `checkout`.

---

## Связи

```
Cart
├── CartItem (1:N) → SKU → PriceHistory (цена, валюта)
│                         → source_object (GFK → модель оборудования)
│                         → ExchangeRate (конвертация в RUB)
├── CartEvent (1:N) — аудит
├── User / session_key — владелец
├── ProjectCustomer — клиент
└── ClientRequest — созданная заявка

Catalog API ← прокси ← CartItem.sku.source_object → ProductDetail
```

---

## Команды

```bash
# Очистка старых анонимных корзин
python manage.py cleanup_anonymous_carts --days 30 --dry-run
python manage.py cleanup_anonymous_carts --days 30

# Тесты
python manage.py test cart --noinput --keepdb
```

---

## Осталось на будущее

- Реальная конвертация `checkout` в `ClientRequest` (позиции → требования)
- Экспорт корзины в Word/Excel
- Интеграция со скидками и персональными ценами клиента
- Объединение нескольких корзин
