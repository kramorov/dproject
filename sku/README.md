# sku — Справочник номенклатуры

Единый реестр товаров/услуг для всего проекта.

**Дата:** 2026-05-21

---

## Назначение

SKU (Stock Keeping Unit) — сквозной справочник, к которому привязываются:
- Модели оборудования (через `SKUMixin`)
- Цены (`PriceHistory.sku`)
- Документы цен, счета, КП

Позволяет:
- Вести позиции без модели — просто код, название, описание
- Унифицировать поиск и фильтрацию цен (один FK вместо GFK)
- Автоматически синхронизировать данные из моделей оборудования

---

## Модель SKU

| Поле | Тип | Описание |
|---|---|---|
| `code` | CharField(100) unique | Уникальный артикул |
| `name` | CharField(300) | Наименование |
| `description` | TextField | Описание |
| `equipment_type` | FK → EquipmentType | Тип оборудования |
| `brand` | FK → Producer | Бренд |
| `source_*` | GFK → модель | Кто создал запись |
| `extra` | JSONField | Произвольные параметры |
| `is_active` | BooleanField | Активность |

---

## SKUMixin

Абстрактная модель (`class Meta: abstract = True`). Добавляет поле `sku` (OneToOneField) и метод `sync_sku()`.

### Подключение к модели

```python
from sku.models import SKUMixin

class GearBox(SKUMixin, models.Model):
    code = models.CharField(...)
    name = models.TextField(...)

    # sku — уже есть из миксина (OneToOneField)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.sync_sku()
```

### Хуки (переопределить при необходимости)

```python
def get_sku_code(self):             # → self.code
def get_sku_name(self):             # → str(self) → self.name → code
def get_sku_description(self):      # → self.description
def get_equipment_type_for_sku(self): # → self.equipment_type
def get_brand_for_sku(self):        # → self.brand
```

### Логика sync_sku()

- При первом save: `get_or_create(SKU, code=...)` → `update(sku=sku)`
- При повторном save: обновляет `name`, `description`, `equipment_type`, `brand` в SKU если изменились
- Если кода нет — выходит молча (SKU не создаётся)

---

## Связь с ценами

`PriceHistory.sku` — FK на SKU (добавлен в миграции `0005`). GFK-поля сохранены для совместимости.

```python
# Старый способ (GFK)
PriceHistory.get_current_price(instance, variety)

# Новый способ (SKU)
PriceHistory.get_current_price_by_sku(sku, variety)
```

---

## API

Пока нет отдельного API — SKU отдаётся через:
- `PriceHistory.get_compact_data()` → `sku_id`, `sku_code`, `sku_name`
- `PriceDocumentDetailView.get()` — через items

Планируется: `/api/admin/sku/` для поиска и фильтрации.

---

## Админка

`/admin/sku/sku/` — список с поиском, фильтрами, импортом/экспортом, подсчётом цен.

---

## Консольные команды

```bash
# gearbox
python manage.py sync_gearbox_sku
```

---

## Миграции

| Файл | Что |
|---|---|
| `sku/0001_initial.py` | CREATE TABLE sku_sku |
| `sku/0002_sku_description.py` | ADD description |
| `price/0005_pricehistory_sku.py` | ADD sku FK + indexes |

---

## Что дальше

- Проверить связку SKU ← цены: создание документа, проведение, срез
- Массовое создание SKU для всех моделей с `code`
- API для поиска SKU
- Замена GFK на SKU в PriceHistory и PriceDocumentItem
- Перенос существующих цен на SKU
