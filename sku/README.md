# sku — Справочник номенклатуры

Единый реестр товаров/услуг для всего проекта.

**Дата:** 2026-05-22

---

## Назначение

SKU (Stock Keeping Unit) — сквозной справочник:
- Модели оборудования (через `SKUMixin`)
- Цены (`PriceHistory.sku` — FK, CASCADE)
- Документы цен (`PriceDocumentItem.sku`)
- Счета, КП

Позволяет:
- Вести позиции без модели — просто код, название, описание
- Унифицировать поиск и фильтрацию цен (один FK вместо GFK)
- Постепенно мигрировать на сущности Django: номенклатура создаётся раньше,
  модель «подхватывает» существующую SKU и обогащает её полями

---

## Модель SKU

| Поле | Тип |
|---|---|
| `code` | CharField(100) unique |
| `name` | CharField(300) |
| `description` | TextField |
| `equipment_type` | FK → EquipmentType |
| `brand` | FK → Producer |
| `source_*` | GFK → модель-источник |
| `extra` | JSONField |
| `is_active` | BooleanField |

---

## SKUMixin

Абстрактная модель: `sku` (OneToOneField) + `sync_sku()`.

### Логика sync_sku()
1. Модель уже привязана к SKU → обновить поля из модели
2. Привязки нет → поиск SKU по коду (get_or_create):
   - Код новый → создать SKU
   - **SKU уже существует** (standalone для счетов/КП) → «подхватить»:
     обогатить name, description, equipment_type, brand, source_*
3. Кода нет → выход

### Подключение
```python
from sku.models import SKUMixin
class GearBox(SKUMixin, models.Model):
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.sync_sku()
```

---

## Связь с ценами

`PriceHistory.sku` — FK (CASCADE). При удалении SKU — каскадное удаление цен.

```python
PriceHistory.get_current_price(instance, variety)     # GFK (совместимость)
PriceHistory.get_current_price_by_sku(sku, variety)   # SKU (основной)
```

`PriceDocumentItem.sku` — FK (PROTECT). Позиции документа привязаны к номенклатуре.

---

## API

| Метод | URL | Описание |
|---|---|---|
| GET | `/api/admin/sku/` | Список (search, brand_id, equipment_type_id) |
| POST | `/api/admin/sku/batch/` | Групповое обновление ({ids, equipment_type_id?, brand_id?}) |
| CRUD | `/api/core/` | Через UniversalAPIView: `model=sku.SKU` |

---

## Фронтенд

`frontend/src/apps/sku-admin/`
- **Список** — поиск, фильтры (тип, бренд), кнопка «Создать»
- **Форма CRUD** — модальное окно (код, название, описание, тип, бренд)
- **Групповая обработка:**
  - Фильтры: код (подстрока), тип (с «не указано»), бренд (с «не указано»)
  - Чекбоксы, «Выделить всё/Снять»
  - «Отобрать по фильтрам» — обновление списка
  - «Записать» — установить тип/бренд выделенным

---

## Админка

`/admin/sku/sku/` — поиск, фильтры, импорт/экспорт, list_editable.

---

## Консольные команды

```bash
python manage.py sync_gearbox_sku
```

---

## Миграции

| Файл | Что |
|---|---|
| `sku/0001_initial.py` | CREATE TABLE |
| `sku/0002_sku_description.py` | ADD description |
| `price/0007_pricehistory_sku.py` | ADD sku FK + indexes |
| `price/0008_link_pricehistory_to_sku.py` | Data: PH → SKU |
| `price/0009_document_to_sku.py` | PriceDocumentItem GFK → sku FK |

---

## Что дальше

- Массовое создание SKU для всех моделей с `code`
- Замена GFK на SKU в PriceHistory (полный переход)
- API для поиска SKU (выполнено)
- Интеграция с 1С
