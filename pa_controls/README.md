# Модуль `pa_controls` — блоки концевых выключателей

## Модели

| Модель | Файл | Описание |
|---|---|---|
| `LimitSwitchBox` | `models/limit_switch.py` | Блок концевых выключателей: серия, корпус, датчики, IP, Exd |
| `LimitSwitchModelLine` | `models/lsb_model_line.py` | Серия БКВ: бренд, шаблоны |
| `LimitSwitchBody` | `models/lsb_body.py` | Корпус БКВ: вес, отверстия под КВ, монтаж |
| `LimitSwitchSensorVariety` | `models/lsb_options.py` | Тип сенсора |
| `SensorComponent` | `models/lsb_options.py` | Датчик: тип сигнала, контактная форма |
| `SignalType` | `models/lsb_options.py` | Тип сигнала |
| `ContactForm` | `models/lsb_options.py` | Контактная форма |
| `ContactState` | `models/lsb_options.py` | Состояние контакта |

## Наследование LimitSwitchBox

```
CatalogDictMixin   — to_dict(), to_values_dict(), build_schema()
SmartCatalogMixin  — фильтрация и поиск
CopyMixin          — копирование (_copy_custom_relations для M2M)
TemplateMixin      — генерация названия/описания по шаблону
ImageGalleryMixin  — галерея изображений
TechDocMixin       — техническая документация
SKUMixin           — привязка к номенклатуре
```

## Структура to_dict()

```python
{
    "id": 1, "code": "LSB-1", "name": "...",
    "model_line": {"id": 1, "name": "LSB Series", "brand": {...}},
    "sku": {"id": 1, "code": "LSB-1", "name": "..."},
    "template_vars": {
        "code", "name", "model_line_name", "brand_name",
        "sensor_variety", "points", "ip", "exd",
        "work_temp", "work_temp_min", "work_temp_max",
        "body_material", "body_material_specified",
        "weight", "cable_glands_holes", "mounting",
        "is_pneumatic", "has_namur_interface", "has_visual_indicator",
        "primary_sensor", "primary_sensor_signal_type",
        "sensors", "sensors_description", "signals",
        "cert_description"
    },
    "sections": [
        {"key": "images", "type": "gallery"},
        {"key": "specs", "type": "specs", "groups": [
            {"key": "general", "title": "Основные", "fields": [...]},      # 9 полей
            {"key": "body", "title": "Корпус", "fields": [...]},           # 5 полей
            {"key": "sensors", "title": "Датчики", "fields": [...]},       # 4 поля
            {"key": "conditions", "title": "Условия эксплуатации"},        # 1 поле
        ]},
        {"key": "docs", "type": "files"},
        {"key": "certs", "type": "files"},
        {"key": "description", "type": "text"},
    ],
}
```

## Фильтры

FILTER_DEFINITIONS:
- model_line_id — серия (EXACT)
- sensor_variety_id — тип сенсора (EXACT, UNIQUE_FIELD_VALUES)
- points — количество датчиков (EXACT, CHOICES: 1-4)
- ip_id — IP (IP_RANK, GLOBAL_MODEL)
- work_temp_min/max — температура (TEMP_MIN/MAX)
- body_material_id — материал корпуса (EXACT)
- model_line_brand_id — бренд серии (EXACT, UNIQUE_FIELD_VALUES)
- signal_type_id — тип сигнала (EXACT, UNIQUE_FIELD_VALUES)
- exd_id — взрывозащита (EXD_COMPATIBLE)
