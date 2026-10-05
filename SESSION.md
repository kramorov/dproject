# SESSION.md — состояние проекта и план Фазы 4 (локализация данных)

Дата: 2026-10-05. Это checkpoint: что сделано, какие решения приняты и подробный план
реализации локализации данных (RU/EN/ZH) на пилоте «БКВ» (`pa_controls`).

---

## 1. Общий статус проекта

### Frontend — готово (собрано, `npm run build` зелёный)
- **Фаза 0 (гигиена):** убран dummy `Authorization` из `frontend/src/services/axios.js`;
  README актуализирован; план в `frontend/docs/migration-plan.md`; GraphQL заморожен.
- **Фаза 1 (auth):** единый store `frontend/src/shared/stores/auth.js`; логин/логаут без
  полной перезагрузки; `?next=` редирект; `name`-атрибуты полей для сохранения пароля.
- **Фаза 2 (URL-каталоги):** `frontend/src/shared/composables/useCatalogRoute.js`
  (SPA — query через vue-router, embed — `location.hash`). Все 9 каталогов переведены
  на URL-управляемый режим (назад/вперёд, deep-link, бредкрамбы из маршрута).
- **Фаза 3 (i18n UI-хрома):** лёгкий модуль `frontend/src/shared/i18n/` + словари
  `ru/en/zh`; префикс локали `/en/`, `/zh/` (ru без префикса) через `expandRoutes()` в
  `frontend/src/router/index.js` + guard `meta.locale`; переключатель в шапке; переведены
  Header, TopMenu, CatalogActions (табы), auth-страницы, modeNames/бредкрамбы каталогов.
- **Фаза 4 (фронт-задел):** `frontend/src/shared/api.js` шлёт `Accept-Language`
  (`ru`/`en`/`zh-CN`) в каждом запросе.

### Backend — локализация данных: НЕ начата (этот план)

### Осталось после Фазы 4
- Фаза 5: runtime-проверка standalone-сборок и hash-fallback (нужен запущенный фронт + браузер).

---

## 2. Согласованные решения (не пересматривать без нужды)

1. Локали: `ru` (базовый), `en`, `zh`. URL-префикс `/en/`, `/zh/`, ru — без префикса.
2. GraphQL заморожен, работаем по REST (DRF).
3. SSR (Nuxt) на паузе — держим SPA единообразно с мини-приложениями.
4. Переводы данных — да (не только UI).
5. **Форма хранения:** базовое RU-поле остаётся рабочим (редактируется как раньше);
   рядом добавляется `<field>_i18n` = `JSONField(default=dict)` = `{"ru": "...", "en": "...", "zh": "..."}`.
   При сохранении `ru` синхронизируется в `_i18n["ru"]`. Чтение — только через
   `pick_i18n(field_i18n, locale)` (fallback: `locale → ru → ""`).
6. Шаблоны резолвятся на **2 уровнях**: `model_line` (каталога) → `EquipmentType` (фоллбэк).
7. `name`/`description` — **гибрид**: локализованные шаблоны (источник истины) +
   денормализованный `display_i18n` на айтеме (быстрое чтение списков).
8. **Пилот — БКВ** (`pa_controls`).

---

## 3. Уже готово (Фаза 4, шаг 0)

`core/utils/localization.py` — проверено:
- `pick_i18n(i18n, locale, fallback='ru')` — устойчив к plain-строке (не dict).
- `sync_ru(i18n, ru_value)` — вернуть dict с обновлённым `ru` (не мутирует).
- `set_locale(i18n, locale, value)` — вернуть dict с переводом.
- `locale_from_accept_language(header)` — `Accept-Language → ru|en|zh`.

Проверка: `python manage.py check` → «no issues»; smoke-тест хелперов прошёл.

---

## 4. Подробный план Фазы 4 (пилот БКВ)

### Шаг 1 — локаль-осведомлённый `core/models/mixins.py`

Файл: `core/models/mixins.py` (91 КБ, много подклассов — делать осторожно).

Текущее состояние (важно):
- `generate_name()`, `generate_description()`, `generate_title()`, `generate_spec_title()`,
  `generate_list_title()` вызывают `_fill_template(self.<field>_template, ...)`.
- Свойства `<field>_template` (name/description/title/spec_title/list_title) резолвят цепочку:
  `_get_title_template_source()` / `_get_description_template_source()` (model_line)
  → `_get_equipment_type_template(field)` (EquipmentType) → `_get_default_*_template()`.
- `_fill_template(template, data_dict)` подставляет плейсхолдеры из `_get_data_dict()`,
  а значения резолвит `_resolve_data_dict_target()` (справочники).
- `save()` → `update_name(save=False)` + `update_description(save=False)` (если не
  `skip_auto_generate=True`).

Изменения:
1. Добавить параметр `locale=None` (default `DEFAULT_LOCALE`) во все `generate_*`.
2. Добавить метод `_resolve_template(field_base, locale)`:
   - взять RU-шаблон текущей цепочки (`getattr(self, field_base)` — существующее свойство);
   - взять `_i18n` из ТОГО ЖЕ источника резолва (model_line или EquipmentType);
   - вернуть `pick_i18n(i18n, locale, fallback=ru_template)`.
   ВАЖНО: `_i18n` нужно читать из того же объекта, откуда взят RU-шаблон, чтобы не
   разъехаться (проверить `_get_title_template_source()` и аналоги).
3. `_get_data_dict(locale)` и `_resolve_data_dict_target(locale)` — локализовать значения
   справочников (связано с Шагом 3): `pick_i18n(obj.<field>_i18n, locale)`.
4. `generate_*` передают `locale` в `_fill_template` и в `_get_data_dict`.

Проверка: `manage.py check` + юнит-тест `generate_description('ru') == generate_description('en')`
при пустых переводах (fallback на ru) и различаются при заполненном en.

### Шаг 2 — шаблоны `_i18n` (миграция + sync)

Файлы и поля:
- `core/models/equipment_type.py` (EquipmentType): добавить JSONField `default=dict`:
  `name_template_i18n`, `description_template_i18n`, `title_template_i18n`,
  `spec_title_template_i18n`, `list_title_template_i18n`, `spec_template_i18n`.
- `pa_controls/models/lsb_model_line.py` (БКВ series): добавить
  `name_template_i18n`, `description_template_i18n`.
  (Проверить, есть ли у этой модели `title_template`/`spec_template` — у других каталогов
  есть; у БКВ по факту только name/description, остальное из EquipmentType.)

Миграция:
- `makemigrations` + **data-migration**: для каждой существующей записи с непустым RU-полем
  → `_i18n["ru"] = ru_поле`.
- Синхронизация на save: в `save()` (или сигнал `pre_save`) — `field_i18n = sync_ru(field_i18n, field_ru)`
  для каждого локализуемого поля. `core/utils/localization.py` уже имеет `sync_ru`.

Проверка: `manage.py makemigrations --check` (после миграций), `manage.py migrate`,
ручная проверка в админке/шелл: поменял `title_template` → `title_template_i18n["ru"]` обновился.

### Шаг 3 — справочники БКВ `_i18n`

Файлы (БКВ-справочники, строковые поля `name`/`description`/`text_description`):
- `pa_controls/models/sensor.py` (тип сенсора)
- `pa_controls/models/lsb_body.py` (материал корпуса)
- `pa_controls/models/visual_indicator.py` (визуальный индикатор)
- `pa_controls/models/pa_control_options.py` (опции; ВНИМАНИЕ: там есть свои
  `name_template`/`description_template` — их тоже локализовать как в Шаге 2)
- `pa_controls/models/pa_control_mounting.py` (монтаж)

Изменения:
- Добавить `name_i18n`, `description_i18n` (и `text_description_i18n`, где есть) JSONField `default=dict`.
- Sync ru на save (как в Шаге 2).
- Связать с Шагом 1: `_resolve_data_dict_target(locale)` читает `_i18n`.

НЕ переводить: `symbolic_code`, числовые поля, FK-коды. `choices`-справочники в коде
(`ETT_ACTUATOR_TYPES` и т.п.) — отдельная история (gettext `_()` или вынос в БД), в этот
пилот не входит.

Проверка: тест резолва шаблона с локализованным справочником.

### Шаг 4 — `display_i18n` на айтеме

Файл: `pa_controls/models/limit_switch.py` (и, при необходимости, общий миксин).

Изменения:
- Добавить `display_i18n = JSONField(default=dict)` на айтем.
- В `save()` (после авто-генерации) собрать на каждую локаль из `LOCALES`:
  `{"name": ..., "description": ..., "title": ..., "list_title": ..., "spec_title": ...}`
  через `generate_*(locale)`.
  Итог: `display_i18n = {"ru": {...}, "en": {...}, "zh": {...}}`.
- Инвалидация: перегенерировать на `save()` айтема; при изменении шаблона/справочника —
  либо сигнал, либо management-команда массового пересчёта (на пилоте — команда или ручной запуск).

Проверка: тест — создал айтем → `display_i18n` содержит все 3 локали; изменил шаблон →
  после пересчёта `display_i18n` обновился.

### Шаг 5 — сериализаторы/вью читают локаль

Файлы:
- `pa_controls/catalog/views_list.py`, `views_detail.py`, `views_engineer.py`, `views_filters.py`, `views_quickselect.py`, `views/meta.py`, `views/catalog.py`.
- `core/models/catalog_serializer.py` (общий сериализатор каталога + `spec_download_url`).

Изменения:
- Локаль из `request.headers['Accept-Language']` → `locale_from_accept_language()`.
- Отдавать локализованные поля: name/description/title — из `display_i18n[locale]`
  (fallback ru), а не из сырых `name`/`description`.
- Мета/фильтры: подписи фильтров и значения справочников — через `_i18n`.
- `label`/`description` справочников в `views/meta.py` и `filter_defs.py` — локализовать.

Проверка: ручной/авто-тест API с заголовком `Accept-Language: en` возвращает en-поля.

### Шаг 6 — спецификация `.docx` на локаль

Файл: `core/models/spec_docx.py` (+ `core/models/mixins.py` для контекста).

Изменения:
- `render_spec_docx(item, locale=None)` — пробросить локаль.
- Заголовок: `generate_spec_title(locale)` (локализованный `spec_title_template`).
- Подписи групп/полей: `spec_template_i18n[locale]` (локализованный `{"группа": {"подпись": ключ}}`).
- Значения полей: из справочников с `_i18n` (Шаг 3).
- Хром документа («Спецификация»/«Specification» и шапка) — отдельный локализованный
  словарь/JSON на уровне рендерера (позже).

Проверка: генерация `.docx` для `ru` и `en` → заголовок и подписи различаются.

---

## 5. Верификация на каждом шаге

- `python manage.py check` — после каждой правки моделей/mixins.
- `python manage.py makemigrations pa_controls core --check` — миграции в норме.
- `python manage.py migrate` — только после makemigrations.
- Юнит-тест на fallback (`pick_i18n`): `en` отсутствует → возвращается `ru`.
- `frontend`: `npm run build` (не должен ломаться — бэкенд-правки не влияют, но проверить).

---

## 6. Риски и открытые вопросы

- **`mixins.py` большой и общий** — правки локали затрагивают все каталоги, не только БКВ.
  Делать через `locale=None` (default ru), чтобы поведение остальных каталогов не изменилось.
- **`spec_template` — вложенный JSON** (`{группа: {подпись: ключ}}`); локализованная форма
  `{"ru": {...}, "en": {...}, "zh": {...}}` — локаль как внешний ключ. Не перепутать с
  плоскими `*_template_i18n`.
- **Синхронизация ru→`_i18n["ru"]`**: решить, делать в `save()` или в `pre_save`-сигнале,
  чтобы не зациклить (не вызывать повторный `save()` из `sync_ru`).
- **Массовая перегенерация `display_i18n`** при изменении шаблона/справочника — нужна
  management-команда (на пилоте достаточно ручного запуска).
- **`choices`-справочники в коде** (ett и др.) — вне пилота; позже gettext `_()` или вынос в БД.
- **Аудит `_()`**: НЕ везде обёрнуто (ai_assistant, configurator, assemblies, ett, gearbox,
  image_processor, media_library, частично electric_actuators/core). Отдельная задача по статике,
  вне пилота.

---

## 7. Что делать первым при возврате к реализации

1. `core/models/mixins.py` — `locale`-параметр в `generate_*` + `_resolve_template(locale)`
   + `_get_data_dict(locale)`/`_resolve_data_dict_target(locale)`. (Шаг 1)
2. Миграции шаблонов `_i18n` (EquipmentType + lsb_model_line) + data-migration + sync ru. (Шаг 2)
3. Дальше по шагам 3→6, с `manage.py check` после каждого.
