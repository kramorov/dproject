# Model Introspector — размотка Django-моделей в ETP

> Снапшот: 2026-08-12

## Назначение

Скрипт `_introspect_model.py` «разматывает» модель оборудования через FK/OneToOne/M2M
цепочки и собирает **все reachable поля** в плоский список. Результат используется как
источник для заполнения `EquipmentTypeParameter` (ETP) — единой таблицы параметров.

Проблема, которую решает интроспектор: поля подбора рассредоточены по нескольким моделям
(`model_line`, `model_line_item`, `body`, through-модели M2M). Вручную поддерживать список
параметров для каждого типа оборудования — дорого и ошибочно. Интроспектор автоматически
собирает всё из Django Meta.

## Принцип работы

```
EquipmentType (code='lsb')
    └── content_type → pa_controls.LimitSwitchBox (Django model)
            ├── Level 0: прямые поля модели
            │     body, ip, exd, model_line, work_temp_min, ...
            └── Level 1: поля через один FK (цепочка field__subfield)
                  body__weight, body__mounting, model_line__brand, ...
```

Алгоритм:
1. По `code` типа оборудования находим `content_type` → Django model class.
2. Рекурсивно обходим `model._meta.get_fields()`.
3. Для каждого поля определяем тип (`fk`, `m2m`, `integer`, `boolean`, ...).
4. FK/OneToOne → добавляем само поле (`body`) и, при depth < max, разматываем связанную
   модель с префиксом (`body__weight`).
5. M2M → добавляем поле, но НЕ разматываем (для UI это просто мультиселект).
6. Для каждого поля инферим `filter_type` и `data_source_type`.

## Инференция типов

| Django-тип поля | filter_type | data_source_type | Пояснение |
|---|---|---|---|
| `ForeignKey` | `exact` / `choice` | `foreign_key` | `choice` если в target есть `material`/`brand` |
| `ManyToManyField` | `choice` | `global_model` | мультиселект из справочника |
| `IntegerField` и др. | `gte` | `field_values` | числовой диапазон |
| `BooleanField` | `boolean` | `choices` | да/нет |
| `CharField`/`TextField` | `icontains` | `field_values` | текстовый поиск |
| `JSONField` | `icontains` | `field_values` | свободный JSON |

## Исключения (skip-правила)

Поля, которые НЕ попадают в снапшот:

- **Служебные**: `id`, `sorting_order`, `is_active`, `created_at`, `updated_at`, `uuid`, `slug`, ...
- **Медиа/файлы**: `image*`, `FileField`, `ImageField`, `BinaryField`
- **Метаданные M2M**: `tech_docs`, `cert_docs`, `image_gallery`, `images`
- **Приватные**: префикс `_`
- **Reverse-relations**: автосозданные `*_set`

## Использование

```bash
# Просто посмотреть поля (без записи)
python _introspect_model.py lsb

# С глубиной 3 (FK-цепочки через 2 уровня)
python _introspect_model.py directional-valve --depth 3

# Сравнить с существующими ETP (diff)
python _introspect_model.py lsb --diff

# JSON-вывод (для интеграции)
python _introspect_model.py pneumatic-actuator --json

# Записать результаты в ModelFieldSnapshot (БД)
python _introspect_model.py lsb --save

# Перенести активные поля из снапшота в ETP
python _introspect_model.py lsb --sync-etp
```

## Модель ModelFieldSnapshot

Результаты интроспекции хранятся в `configurator.ModelFieldSnapshot` — чтобы не прогонять
интроспекцию каждый раз и сохранять пользовательские правки.

```
ModelFieldSnapshot
├── equipment_type → FK(EquipmentType)
├── field_path      ← реальный путь в Django ('work_temp_min', 'body__weight')
├── param_name      ← канонический ключ ('temp_min', 'ip_id') — синхронизация
├── field_type      ← fk, m2m, integer, boolean, ...
├── target_model    ← app_label.ModelName для FK/M2M
├── source_model    ← где поле определено
├── depth           ← 0 = прямое, 1 = через FK
├── filter_type     ← exact, choice, gte, boolean, icontains
├── data_source_type← foreign_key, global_model, field_values, choices
└── is_active       ← включать ли в ETP
```

### Unique constraint

`(equipment_type, field_path)` — одно поле модели = одна запись снапшота. При повторном
запуске интроспектора записи **обновляются**, а не дублируются. Поля, которые исчезли
из модели, помечаются `is_active=False` (не удаляются).

## Синхронизация field_path ↔ param_name

Ключевая проблема: в разных моделях одно и то же понятие называется по-разному.

| Понятие | param_name (канон) | field_path (в моделях) |
|---|---|---|
| Мин. температура | `temp_min` | `work_temp_min`, `temperature_min` |
| IP-защита | `ip_id` | `ip` (FK), `ip` (CharField) |
| Материал корпуса | `body_material_id` | `body_material` (FK), `body__material` |

Решение — двухуровневая схема:
- **`field_path`** — то, что видит интроспектор (реальные Django-имена).
- **`param_name`** — канонический ключ, который назначает человек/скрипт. AI и UI работают
  ТОЛЬКО с `param_name`. Один `param_name` объединяет разные `field_path` из разных моделей.

`param_name` и есть тот самый «ключ синхронизации» — он уже есть в `EquipmentTypeParameter`.

## Перенос в ETP

`sync_to_etp()` переносит активные снапшоты в ETP:

```
ModelFieldSnapshot (is_active=True)
    └── sync_to_etp()
          └── EquipmentTypeParameter
                ├── param_name   = snapshot.param_name (или field_path, если пусто)
                ├── field_path   = snapshot.field_path
                ├── filter_type  = snapshot.filter_type
                ├── data_source_type = snapshot.data_source_type
                ├── product_model = equipment_type.content_type
                └── is_active    = True
```

## Сценарий: добавление нового поля в модель

1. Разработчик добавил поле `vibration_resistance` в `LimitSwitchBody`.
2. Запускаем `python _introspect_model.py lsb --save --diff`.
3. Интроспектор находит новое поле `body__vibration_resistance` — показывает как NEW.
4. В админке/скрипте ставим `param_name='vibration_resistance'`, `is_active=True`.
5. `--sync-etp` переносит в ETP → появляется в AI и UI.

Без переписывания кода, без ручного поиска по моделям.

## TODO / ограничения

- Инференция `filter_type` пока эвристическая — для `exd` (M2M на ExdOption) нужна
  `exd_compatible`, а не `choice`. Требует доработки правил.
- `depth=2` даёт много шума (метаданные, шаблоны). Возможно, для ETP нужен только Level 0
  + избранные FK-цепочки.
- Нет UI-редактора для `param_name` — сейчас назначается через скрипт/админку.
- `options_config` для `global_model` M2M не заполняется автоматически (нужен маппинг
  target_model → справочник).
