# SESSION.md — состояние проекта и план Фазы 4 (локализация данных)

Дата: 2026-10-05. Это checkpoint: что сделано, какие решения приняты и подробный план
реализации локализации данных (RU/EN/CN) на пилоте «БКВ» (`pa_controls`).

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
  `ru/en/cn`; префикс локали `/en/`, `/cn/` (ru без префикса) через `expandRoutes()` в
  `frontend/src/router/index.js` + guard `meta.locale`; переключатель в шапке; переведены
  Header, TopMenu, CatalogActions (табы), auth-страницы, modeNames/бредкрамбы каталогов.
- **Фаза 4 (фронт-задел):** `frontend/src/shared/api.js` шлёт `Accept-Language`
  (`ru`/`en`/`zh-CN`) в каждом запросе.

### Backend — локализация данных: ФАЗА 4 ЗАВЕРШЕНА (шаги 0→6, см. раздел 3)

### Осталось после Фазы 4
- Фаза 5: runtime-проверка standalone-сборок и hash-fallback (нужен запущенный фронт + браузер).

---

## 2. Согласованные решения (не пересматривать без нужды)

1. Локали: `ru` (базовый), `en`, `cn` (китайский). Код везде `cn`, не `zh`/`zh-CN`;
   Accept-Language `zh-CN` мапится в `cn`. URL-префикс фронта — `/en/`, `/cn/`
   (переименовано из `/zh/`; `npm run build` зелёный).
2. GraphQL заморожен, работаем по REST (DRF).
3. SSR (Nuxt) на паузе — держим SPA единообразно с мини-приложениями.
4. Переводы данных — да (не только UI).
5. **Форма хранения:** базовое RU-поле остаётся рабочим (редактируется как раньше);
   рядом добавляется `<field>_i18n` = `JSONField(default=dict)` = `{"ru": "...", "en": "...", "cn": "..."}`.
   При сохранении `ru` синхронизируется в `_i18n["ru"]`. Чтение — только через
   `pick_i18n(field_i18n, locale)` (fallback: `locale → ru → ""`).
   **RU-значения в БД остаются как есть**: рабочие RU-поля никуда не переезжают,
   en/cn — только расширение `_i18n`.
6. Шаблоны резолвятся на **2 уровнях**: `model_line` (каталога) → `EquipmentType` (фоллбэк).
7. `name`/`description` — **гибрид**: локализованные шаблоны (источник истины) +
   денормализованный `display_i18n` на айтеме (быстрое чтение списков).
8. **Пилот — БКВ** (`pa_controls`).
9. Названия серий (`model_line.name`) — **торговые названия, НЕ локализуются** (до отдельного
   решения пользователя, 2026-10-05). Коды (`code`/`symbolic_code`/FK-коды) НЕ локализуются никогда.
10. Локаль данных — заголовок `Accept-Language`; gettext-хром (заголовки секций и т.п.) — `?lang=`.
    Вне пилота: question_graph/wizard/constructor-эндпоинты и CUSTOM/cascade-опции фильтров
    остаются ru (механизм есть — пробросить заголовок позже).

---

## 3. Уже готово (Фаза 4, шаг 0)

`core/utils/localization.py` — проверено:
- `pick_i18n(i18n, locale, fallback='ru')` — устойчив к plain-строке (не dict).
- `sync_ru(i18n, ru_value)` — вернуть dict с обновлённым `ru` (не мутирует).
- `set_locale(i18n, locale, value)` — вернуть dict с переводом.
- `locale_from_accept_language(header)` — `Accept-Language → ru|en|cn` (`zh*` → `cn`).
- `LOCALES = ("ru", "en", "cn")`, `DEFAULT_LOCALE = "ru"`.
- Тестовая БД `test_db.sqlite3` — свежая копия боевой (см. раздел 8).

### Шаг 1 — локаль-осведомлённый TemplateMixin — СДЕЛАНО (2026-10-05)

- `core/models/mixins.py`: `generate_* (locale=None)`, `_resolve_template(field_base, locale)`,
  `_get_template_i18n(field_base)` (перевод из ТОГО ЖЕ источника, откуда взят RU-шаблон),
  `_get_data_dict(locale=None)`, `_resolve_data_dict_target(target, locale)` +
  `_get_target_i18n(target)` (локализация значений справочников), `_fill_template(..., locale=None)`.
  Рефакторинг: `_get_equipment_type()` выделен из `_get_equipment_type_template()`.
- `core/utils/localization.py`: `pick_i18n` — fallback-значение (не код локали) возвращается
  при отсутствии перевода; поведение по умолчанию (locale → ru → '') не изменилось.
- `pa_controls/models/sensor.py`: сигнатура `_get_data_dict(self, locale=None)`.
- Тесты: `core/tests/test_localization.py` — 6 тестов (SimpleTestCase, без БД):
  ru default, en-перевод шаблона+справочника, fallback ru без переводов, частичный перевод,
  пустой `_i18n` dict, источник EquipmentType. Все зелёные.
- Smoke на реальных данных (копия боевой): БКВ айтем pk=1 — ru/en/cn идентичны
  (переводов ещё нет), генерация по цепочке работает.
- Ревью-фиксы (2026-10-05): `_get_template_i18n` сверяет источник с `model_line.<field>`
  (перевод из model_line применяется, только если RU-шаблон реально оттуда; у сенсоров
  источник — `variety`, переводы молча не применяются и не «разъезжаются»); редирект
  `/zh/...` → `/cn/...` на фронте; `test_db.sqlite3` убран из git (`.gitignore`);
  тесты на `locale_from_accept_language` и на guard источника.

### Шаг 2 — шаблоны `_i18n` — СДЕЛАНО (2026-10-05)

- Поля: EquipmentType — 6 JSONField (`name/description/title/spec_title/list_title_template_i18n`,
  `spec_template_i18n` — локаль внешним ключом `{"ru": {...}, "en": {...}, "cn": {...}}`);
  LimitSwitchModelLine — `name_template_i18n`, `description_template_i18n` (title/spec у БКВ
  из EquipmentType, как и предполагалось).
- Sync на save: в `save()` обеих моделей — `field_i18n = sync_ru(field_i18n, field_ru)`
  (без рекурсии; en/cn не затираются — проверено).
- Миграции: core 0023 (схема) + 0024 (data-backfill ru); pa_controls 0068 (схема) + 0069
  (data-backfill). Применены к боевой и к копии. `makemigrations --check` — «No changes detected».
- Проверки: backfill — 11 EquipmentType / 5 серий БКВ, все `_i18n["ru"]` == RU-полю;
  sync на save + сохранение en-перевода — ок; 9/9 тестов зелёные.

### Шаг 3 — справочники БКВ `_i18n` — СДЕЛАНО (2026-10-05)

- Новый абстрактный миксин `LocalizedDictFieldsMixin` (core/models/mixins.py): поля
  `name_i18n`/`description_i18n` + `save()` → `_sync_localized_ru()` (переопределяется).
- Применён к справочникам БКВ: SignalType, ContactState, ContactForm, PointsOption,
  LimitSwitchSensorVariety, PaControlMountingStandard, LimitSwitchBody, VisualIndicatorType.
- LimitSwitchSensorVariety дополнительно: `name_template_i18n`, `description_template_i18n`
  + sync; `SensorComponent._get_template_i18n()` читает переводы из variety (источник шаблона).
- Миграции: pa_controls 0070 (схема, 18 полей) + 0071 (data-backfill ru). Применены к боевой
  и к копии; `makemigrations --check` — чисто.
- Проверки: backfill по всем 8 моделям — `_i18n["ru"]` == RU-полю; sync на save + en
  сохраняется; интеграция — `variety.name_i18n["en"]` попадает в `generate_name("en")`
  реального БКВ (таргет `sensor_variety__name`); перевод variety-шаблона попадает в имя
  сенсора (`EN-VARIETY SNI...`).
- Резолверы (`get_brand_name`, `get_primary_sensor_contact_form` и т.п.) — ОСТАЮТСЯ ru
  (решение: локализация резолверов — вне пилота, отдельная задача).
- Вне пилота (follow-up): материалы приложения `materials` (MaterialGeneral/
  MaterialSpecified — кормят `{body_material*}` в шаблонах БКВ) и bare-FK таргеты
  (`{points}` → str(points_option)) — локализация позже.
- Ревью-фиксы Шагов 2-3 (2026-10-05): нормализованы переводы строк LF→CRLF
  (equipment_type.py, visual_indicator.py); добавлен тест `_sync_localized_ru`
  (LocalizedDictFieldsMixinTests); правило sync-контракта — в разделе 8.

### Шаг 4 — `display_i18n` на айтеме — СДЕЛАНО (2026-10-05)

- `TemplateMixin.build_display_i18n()`: {локаль: {name, description, title, list_title,
  spec_title}} через `generate_*(locale)` для всех трёх локалей.
- `LimitSwitchBox`: поле `display_i18n` (JSONField default=dict); в `save()` пересчитывается
  (флаг `skip_display_i18n=True` — для массовых/точечных обновлений).
- Management-команда `rebuild_display_i18n [--limit N]` — массовый пересчёт через
  queryset.update (без save()/sync_sku); запущена: 100/100 на боевой и копии.
- Миграция pa_controls 0072 (схема). Применена к обеим БД.
- Тесты: `pa_controls/tests.py` (DisplayI18nTests, TestCase на копии — транзакционные):
  все локали/поля, соответствие generate_*, отражение правки шаблона после resave,
  skip-флаг. 15/15 тестов (11 локализация + 4 display) зелёные.

### Шаг 5 — API читает локаль — СДЕЛАНО (2026-10-05)

- `CatalogSerializerMixin.to_dict(locale=None)`: name/description/title/image_alt из
  `display_i18n[locale]` (fallback: RU-поля / `generate_title(locale)`); description-секция
  тоже локализована. Default ru — остальные каталоги не изменились.
- `CatalogDictMixin.to_values_dict(locale=None)` — list_title из display_i18n.
- `SmartCatalogMixin.apply_filters_and_split(..., locale=None)` — локаль в сериализатор.
- `FilterDefinition`: параметр `label_i18n`; `get_options(..., locale=None)` — названия опций
  через `localized_name()` (name_i18n справочников).
- `BaseFilterOptionsView` — локаль из `Accept-Language`, label через `pick_i18n(label_i18n, ...)`.
- Вью БКВ (`views_list`, `views_detail`) — локаль из `Accept-Language`.
- БКВ-фильтры (`filter_defs.py`): en/cn-переводы label для всех 13 определений.
- Проверки: smoke на копии (Django test client) — list/detail/filters с `Accept-Language: en`
  отдают en-поля (имя, заголовок, label «Sensor type», опции с переводом), ru без изменений,
  fallback ru для непереведённых опций. 15/15 тестов, `manage.py check` — чисто.
- Вне пилота: template_vars остаются ru; `group`-подписи фильтров не локализуются
  (у БКВ не используются); `lang`-параметр деталки (gettext-хром) не тронут.

### Шаг 6 — спецификация `.docx` на локаль — СДЕЛАНО (2026-10-05)

- `get_spec_doc_context(base_url, locale)`: заголовок из `generate_spec_title(locale)`,
  name/description из display_i18n, `_get_spec_sections(locale)` (сигнатура оверрайдов
  проверяется через inspect — pa_model_line/pneumatic_fittings не сломаны).
- `_get_spec_sections(fields, locale)`: для не-RU берётся `spec_template_i18n[locale]`
  (из ТОГО ЖЕ источника, что RU-шаблон — `_get_spec_template_i18n()`); значения полей
  локализуются в `_resolve_field(spec, locale)` (кэш теперь с локалью).
- `spec_docx.py`: `SPEC_CHROME` (ru/en/cn для «Артикул»/«Характеристики»/«Техдокументация»/
  «Сертификаты»), `build_spec_template` переведён на `{{ chrome.* }}`-плейсхолдеры,
  шаблон перегенерирован (36 790 байт); `render_spec_docx_bytes(..., locale=None)`.
- `spec_doc_views.py`: локаль из `Accept-Language` → рендер.
- Тесты: `SpecDocContextLocaleTests` (контекст без docxtpl) + smoke полного рендера:
  en-docx содержит EN-заголовок/«Specifications»/«Article:»/EN-подписи, ru — прежний.
  20/20 тестов зелёные, `manage.py check` — чисто.

### ФИКС АВТОРИЗАЦИИ (2026-10-05, вне плана Фазы 4)

- Проблема: «двойная авторизация» — пароль хранится в ДВУХ местах: 1:1 Django
  `User.password` (по access.md — источник истины) и `ProjectCustomerUser.password`.
  `CustomerBackend` проверял ТОЛЬКО профиль-хэш, который у всех пользователей пуст
  (реальные хэши — на Django User) → правильный пароль всегда отвергался («Неверный
  email или пароль»), `last_login` у всех None.
- Фикс: `CustomerBackend.authenticate` — пароль проверяется на 1:1 `User` с фоллбэком
  на профиль-хэш (совместимость со старым контрактом); `LoginView` принимает и `email`
  (старый контракт тестов). Проверено на копии: оба хранилища работают, неверный пароль
  отвергается, сессия подхватывается.
- Причина «каталоги не открываются» — бэкенд не был запущен (прокси vite отдаёт 500
  на любой /api/, фронт редиректит на /login). С запущенным бэкендом аноним получает
  права anonymous_users и каталоги открываются (проверено: 200 на catalog/filters).

### Проверка в живом браузере (Phase 5, частично — 2026-10-05)

- Headless Chrome (dump-dom, выполняет JS): `/`, `/en/`, `/cn/` — html lang ru/en/zh-CN,
  топ-меню «Каталоги»/«Catalogs»/«目录», переключатель локали RU/EN/中文 в шапке с
  активным состоянием, ссылки локализованы (`/login`, `/en/login`, `/cn/login`).
- `/login` — форма с полями username/password рендерится; `/catalog/limit-switch` —
  каталог БКВ открывается анонимно (84 КБ DOM, каталог-приложение загружено).
- API через прокси (5173→8000): filters/catalog 200 анонимно; login — 400 с правильной
  ошибкой при неверном пароле. Полный логин с реальным паролем — проверить пользователю.
- НЕ проверено (нужен прод-режим): standalone-сборки с hash-фоллбэком (npm run build +
  раздача через Django) — отдельная задача.

### Фикс UI-хрома каталога БКВ (2026-10-05, после отчёта пользователя)

- Проблема: на `/en/catalog/limit-switch` карточки серий показывали «Серия АМУР» с ru-хромом.
- Причина: в общем `CatalogSection.vue` захардкожены «Серия»/«Обновление…»/«Нет доступных
  серий»; в `apps/limit-switch-catalog/App.vue` — ru-объект `labels` и `eq-name="БКВ"`.
- Фикс: строки переведены на `t()`; в словари ru/en/cn добавлены ключи `catalog.*` (общие:
  seriesPrefix, updating, noSeries, items, search, found, backToCatalog...) и `lsb.*`
  (заголовки БКВ, фильтры, хлебные крошки). Названия серий («АМУР»/«ЯМАЛ») — торговые,
  остаются ru по решению раздела 2 п.9.
- Проверено headless Chrome: ru «Серия АМУР», en «Series АМУР», cn «系列 АМУР», subtitles
  локализованы. Vite dev пересобрал; прод-билд — пересобрать (`npm run build`).
- Follow-up: тот же хардкод-паттерн в мини-приложениях других каталогов (gearbox, cable-gland
  и др.) — перевести по аналогии; описания серий (данные) остаются ru.

### Контент переводов БКВ + доработки пайплайна (2026-10-05)

- Залиты переводы (en/cn) в боевую БД: шаблоны ET8 (name/description/title/spec_title/list_title
  + spec_template подписи), шаблоны и описания 5 серий БКВ, справочники (9 типов сенсора,
  12 типов сигнала, 4 формы/4 состояния контактов, точки, индикаторы) и материалы
  (MaterialGeneral 8, MaterialSpecified 2).
- Новые поля: `LimitSwitchModelLine.description_i18n` (описание серии; название — торговое,
  не переводится); материалы `MaterialGeneral`/`MaterialSpecified` — `LocalizedDictFieldsMixin`
  (name/description_i18n). Миграции materials 0009/0010, pa_controls 0073/0074.
- API: `sections/` и `_get_model_line_summary(locale)` отдают переведённое описание серии.
- Пайплайн (mixins): bare-FK таргеты (`points_option`) и resolver-объекты локализуются через
  `localized_name()`; служебные RU-слова (`Нет`→No/无 и т.п. из `exd_display`) — через
  `localize_service_word()`.
- Проверено на API: EN-имя «Limit switch box ЯМАЛ; 2 sensors, sensor type: Mechanical, Dry
  contact, SPDT single-pole double-throw; IP67, Explosion protection: No; … Anodized
  aluminium»; CN-имя полностью на китайском; опции фильтров EN/CN; описания секций EN/CN.
  Браузер: карточка серии на /en/ — EN-описание. 20/20 тестов. Бэкенд перезапущен.
- Известный остаток: строки «или» внутри `cable_glands_holes_list_text`/`mounting_list_text`
  (технические обозначения с ru-соединителем) — не локализуются.

### Фикс деталки (CatalogDetail) — заголовки и значения секций (2026-10-05)

- Проблема: на en-деталке заголовки секций («Характеристики», «Сертификаты») и часть
  значений/подписей оставались ru.
- Фикс: заголовки секций `to_dict()` переведены с gettext на словарь `_SECTION_TITLES`
  (ru/en/cn) с пробросом locale через `_build_sections` → `_build_specs_section` →
  `_get_spec_sections(locale)`; фоллбэк `_build_model_code_spec(locale)` — тоже.
- `_resolve_field(spec, locale)`: цель локализации — `name_path` (bare-FK/resolver-объекты:
  `points_option`, `get_primary_sensor_contact_form` и т.п.) с фоллбэком на `path`.
- `localize_service_word`: добавлены подстроковые замены единиц/соединителей
  (`°С`→`°C`, `кг`→`kg`, ` или `→` or `/ 或`, `квадрат`→`square`/`方`).
- Проверено: EN-деталка — Images/Specifications/Technical documentation/Certificates/
  Description; группы General/Body/Feedback signals/Sensors; значения `2 sensors`, `No`,
  `-63...+80 °C`, `Anodized aluminium`, индикатор переведён; CN — полностью на китайском
  (включая «方 11» в монтаже). 20/20 тестов, бэкенд перезапущен.

### Фикс QuickSelect (2026-10-05)

- Проблема: заголовки/чипы быстрого подбора оставались ru (хардкод в QuickSelect.vue +
  ru-определения фильтров в вью).
- Фикс: `QuickSelect.vue` — «Серия»/«Модель не найдена»/бредкрамбы через `t()`;
  `BaseQuickSelectView` — локаль из `Accept-Language`: `to_dict(locale)`, опции через
  `localized_name()`, `filter_labels` через `pick_i18n(label_i18n, ...)`;
  `LimitSwitchBoxQuickSelectView` переведён на каталожные `LIMIT_SWITCH_FILTER_DEFINITIONS`
  (с label_i18n; param/model_field идентичны модельным).
- Проверено: EN-чипы «Series/Sensor type/Number of sensors/…»; CN-метки китайские; опции
  и карточка локализованы; браузер /en/catalog/limit-switch?mode=quickselect — без ru-строк.
  20/20 тестов, бэкенд перезапущен.

Проверка: `python manage.py check` → «no issues»; smoke-тест хелперов прошёл.

---

## 4. Подробный план Фазы 4 (пилот БКВ)

### Шаг 1 — локаль-осведомлённый `core/models/mixins.py`

**СДЕЛАНО (2026-10-05)** — см. раздел 3, реализация и проверки.

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

**СДЕЛАНО (2026-10-05)** — см. раздел 3.

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

**СДЕЛАНО (2026-10-05)** — см. раздел 3. Резолверы оставлены ru (решение зафиксировано).

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

- ВНИМАНИЕ (ревью): значения, резолвящиеся resolver-методами (`get_brand_name` и т.п.),
  локализацию обходят — решить здесь: передавать `locale` в резолвер или оставить ru.
- Кодовые поля (`*__code`, `*_code`) НИКОГДА не получают `_i18n`: `_get_target_i18n`
  читает `<last>_i18n` и для них (сейчас полей нет → безопасно, но правило закрепить).

Проверка: тест резолва шаблона с локализованным справочником.

### Шаг 4 — `display_i18n` на айтеме

**СДЕЛАНО (2026-10-05)** — см. раздел 3.

Файл: `pa_controls/models/limit_switch.py` (и, при необходимости, общий миксин).

Изменения:
- Добавить `display_i18n = JSONField(default=dict)` на айтем.
- В `save()` (после авто-генерации) собрать на каждую локаль из `LOCALES`:
  `{"name": ..., "description": ..., "title": ..., "list_title": ..., "spec_title": ...}`
  через `generate_*(locale)`.
  Итог: `display_i18n = {"ru": {...}, "en": {...}, "cn": {...}}`.
- Инвалидация: перегенерировать на `save()` айтема; при изменении шаблона/справочника —
  либо сигнал, либо management-команда массового пересчёта (на пилоте — команда или ручной запуск).

Проверка: тест — создал айтем → `display_i18n` содержит все 3 локали; изменил шаблон →
  после пересчёта `display_i18n` обновился.

### Шаг 5 — сериализаторы/вью читают локаль

**СДЕЛАНО (2026-10-05)** — см. раздел 3.

Файлы:
- `pa_controls/catalog/views_list.py`, `views_detail.py`, `views_engineer.py`, `views_filters.py`, `views_quickselect.py`, `views/meta.py`, `views/catalog.py`.
- `core/models/catalog_serializer.py` (общий сериализатор каталога + `spec_download_url`).

Изменения:
- Локаль из `request.headers['Accept-Language']` → `locale_from_accept_language()`.
- Отдавать локализованные поля: name/description/title — из `display_i18n[locale]`
  (fallback ru), а не из сырых `name`/`description`.
- Мета/фильтры: подписи фильтров и значения справочников — через `_i18n`.
- `label`/`description` справочников в `views/meta.py` и `filter_defs.py` — локализовать.

Проверка: ручной/авто-тест API с заголовком `Accept-Language: en` (или `zh-CN`) возвращает en-поля (cn-поля).

### Шаг 6 — спецификация `.docx` на локаль

**СДЕЛАНО (2026-10-05)** — см. раздел 3.

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
- Юнит-тесты: `python manage.py test --keepdb` — на копии боевой БД (см. раздел 8).
- `frontend`: `npm run build` (не должен ломаться — бэкенд-правки не влияют, но проверить).

---

## 6. Риски и открытые вопросы

- **`mixins.py` большой и общий** — правки локали затрагивают все каталоги, не только БКВ.
  Делать через `locale=None` (default ru), чтобы поведение остальных каталогов не изменилось.
- **`spec_template` — вложенный JSON** (`{группа: {подпись: ключ}}`); локализованная форма
  `{"ru": {...}, "en": {...}, "cn": {...}}` — локаль как внешний ключ. Не перепутать с
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

1. **Закоммитить сегодняшнюю работу** — всё некоммичено: HEAD=0e29325 «front en»,
   56 изменённых/новых файлов (локализация Фазы 4 + фикс авторизации + user_path_map.md).
2. Задачи локализации из раздела 9 по порядку: (1) имена файлов сертификатов/техдоки и
   медиабиблиотеки; (2) имя файла .docx спецификации; (3) spec_template_i18n остальных
   каталогов; (4) локализация мастера подбора.
3. Затем Фаза 5: runtime-проверка standalone-сборок и hash-fallback (нужен запущенный фронт + браузер).

---

## 8. Тестовая БД — копия боевой

- Тесты гоняем на **копии боевой БД** (`db.sqlite3`): создание тестовой с нуля долгое,
  а в копии все миграции уже применены — прогон быстрый.
- Обновление копии: `sqlite3.exe db.sqlite3 ".backup test_db.sqlite3"` (backup API, безопасно
  при запущенном dev-сервере). Файл копии — `test_db.sqlite3` (уже указан в `settings.py`
  как `TEST.NAME`).
- Запуск тестов: `python manage.py test --keepdb`. **Без `--keepdb` копия уничтожается после
  прогона** — тогда просто пересоздать её заново (команда выше).
- Только `TestCase` (транзакционные тесты, откат). `TransactionTestCase` обрезает таблицы
  и может почистить данные копии. Юнит-тесты локализации — `TestCase`.
- Тесты локализации: `core/tests/test_localization.py` (пакет `core/tests/`; файл `core/tests.py`
  перекрыт пакетом и тест-раннером не запускается — туда не писать). Для Шага 4 — `pa_controls/tests/`.
- Нюанс прогона на копии боевой: 3 старых теста (`test_question_graph_options`, `test_wizard`)
  падают и без правок локализации — ожидают пустую БД (пустой реестр фильтров) или
  несуществующее поле `exd_id`. К локализации отношения не имеют.
- `test_db.sqlite3` — вне git (`.gitignore`): это копия боевых данных, в репозитории
  её быть не должно. `db.sqlite3` (боевая) — ОСТАЁТСЯ в git (решение пользователя, 2026-10-05).
- **Контракт синхронизации ru→`_i18n`**: работает при полном `save()` (админка).
  `save(update_fields=...)` без `_i18n`-полей и `QuerySet.update()` оставляют БД
  несогласованной — правки RU-полей только через полный save; массовые пересчёты —
  `rebuild_display_i18n`.

---

## 9. Задачи локализации (очередь, 2026-10-05)

1. **Названия файлов сертификатов/техдокументации и изображений в медиабиблиотеке.**
   Сейчас имена формируются ru: `core/models/catalog_serializer.py` —
   `_get_certs_section()` (`f"{variety_name} {cert_code} для {ml_name}"`),
   `_build_doc_dict()` (`doc.name`), подписи «Скачать»/«Скачать (сжат)» в
   `core/models/spec_docx.py::_build_rich_links`. Нужно: локализованные имена файлов
   (серия — trade, служебные «для»/«Сертификат» — через локаль), alt-тексты и названия
   в медиабиблиотеке.

2. **Шаблон имени файла спецификации (.docx).** `core/spec_doc_views.py`:
   `filename = 'Спец-я %s.docx'` — сделать из локали (`Accept-Language`):
   ru «Спецификация», en «Spec», cn «规格» и т.п. (Content-Disposition).

3. **Шаблоны спецификаций — локализовать для остальных каталогов.** Для БКВ
   `spec_template_i18n` (EquipmentType) работает (Шаг 6 + контент). Распространить:
   en/cn-переводы `spec_template_i18n` остальных EquipmentType/серий; проверить
   `_get_spec_template_i18n()` для случая собственного `spec_template` серии.

4. **Локализация мастера подбора (Wizard).** `WizardSelection.vue`,
   `QuestionGraphWizard.vue`, `AiSelectionPage.vue` + бэкенд `core/wizard_views.py`,
   `core/question_graph_views.py` — сейчас ru (метки узлов, вопросы, подсказки).
   Задача: пробросить локаль из `Accept-Language` во все wizard-эндпоинты и перевести
   UI-строки через `t()`/словари (как сделано для QuickSelect/деталки).


---

## 10. Сессия 2026-10-06 — справочники/серии: `_i18n` везде + фиксы регрессий

### Сделано

1. **Фиксы регрессий после коммита «locale»:**
   - `CatalogSerializerMixin.to_dict()` стал звать хуки с `locale=`; у каталогов
     переопределения были со старыми сигнатурами → список отдавал только `{id}`.
     Добавлен `locale=None` в `_get_model_line_summary()` (filter_regulator, gearbox,
     solenoid_valves) и `_get_spec_sections()` (pneumatic_fittings).
   - `question_graph_views._get_options_for_param()` падал на `exd_id` (M2M вместо FK):
     добавлена ветка `many_to_many` + использование `field_lookup` вместо `param_name`.
   - Фронт: индексные страницы каталогов (`CatalogEquipmentIndex`/`Valves`/`Solutions`)
     и ссылки «назад в каталоги» переведены на `t()` + `localizedPath()`; локали en/cn
     дополнены.

2. **Миксины локализации (core/models/mixins.py):**
   - `LocalizedDictFieldsMixin` — name + description (справочники).
   - `LocalizedNameFieldsMixin` — только name (справочники без `description`).
   - `LocalizedDescriptionFieldsMixin` — только description (серии без шаблонов).
   - `LocalizedModelLineMixin` — description + `name_template_i18n` +
     `description_template_i18n` (серии с шаблонами).
   - **Фикс partial-save:** все миксины принудительно добавляют свои `_i18n`-поля в
     `update_fields`, чтобы `save(update_fields=['name'])` не рассинхронизировал ru.

3. **Справочники (~99 моделей):** `params` (55), `producers`, `materials` + 14 каталоговых
   приложений (Option/Variety/Type/…). Миграции применены.

4. **Серии (ModelLine):** `name` — торговое, НЕ локализуется; локализуются `description`
   и шаблоны (`name_template`/`description_template`) через `<field>_i18n` JSON
   (из того же источника, что и RU-шаблон). Поля `*_template_i18n` добавлены 7 сериям.

5. **Переводы en/cn:** коды/уникальные названия (Ex db, IP67, NPT/G/M, У1/ХЛ1, T1..T6,
   ГЕРДА, FLEXICON, NAMUR, модели датчиков, размеры) НЕ переводятся (fallback ru).
   - params: data-миграция `params/0071` (50 терминов).
   - каталоговые: команда `translate_reference_dicts` (161 строка).
   - описания серий: команда `translate_model_line_descriptions` (37 описаний).

6. **Конструктор ПП:** `PneumaticBodyDesignOption.body_coating_option` FK на
   `BodyCoatingOption` + backfill; `get_display_name(locale)`; `get_available_options(locale)`
   + проброс `Accept-Language` в `/constructor/options/`.

7. **Фронт:** `index.html` — `translate="no"` + `<meta name="google" content="notranslate">`.

### Команды (идемпотентны)
- `python manage.py backfill_localized_ru` — `_i18n['ru']` для всех `*_i18n`.
- `python manage.py translate_reference_dicts` — en/cn справочников.
- `python manage.py translate_model_line_descriptions` — en/cn описаний серий.

### НЕ сделано (очередь)
- en/cn текст шаблонов `name_template_i18n`/`description_template_i18n` 7 серий (только ru).
- Локализация wizard (задача 4 раздела 9) — не трогалась.
- `EquipmentType.name/description` не локализованы (config-сущность).
- spec/docx filename и названия файлов сертификатов (задачи 1-2 раздела 9).

### Тесты
- `python manage.py test core.tests.test_localization --keepdb` — 11 OK.

---

## 11. Сессия 2026-10-07 — локализация остальных слоёв

Локализация расширена с БКВ-пилота на весь стек. Общий паттерн и чек-лист — в
**`lang.md`** (главный документ для локализации новых моделей).

### Сделано
- **Инженерный подбор (EngineerSelection)**: фильтры/результаты/Exd/Climate/Thread —
  переведены (фронт `t()` + бэкенд `Accept-Language`).
- **Exd/Climate справочники** (`params/exd_models.py`, `core/views.py`,
  `core/climate_views.py`): `description`/`name` методов через `_i18n`; команда
  `translate_exd_climate_descriptions`.
- **Данные датчика** (`pa_controls/models/sensor.py`): `get_exi_params`,
  `extra_params` → `{ru/en/cn}`, `electrical_specs_i18n`; `_call_resolver` передаёт
  локаль резолверам.
- **Спецификация `.docx`**: контент/имя файла/кнопка «Скачать спецификацию» —
  локализованы (`spec_docx.py`, `spec_doc_views.py`, `?lang=` в URL).
- **Имена медиа/сертификатов/изображений** (`MediaLibraryItem`, `CertData`):
  `name_i18n`; `localized_name` в `_build_doc_dict`/`_build_image_dict`/`_get_certs_section`;
  `translate_media_names` (фразовый).
- **Имя файла сертификата**: «для»→«for»/«用于», «(сжат)»→«(compressed)»/«(压缩)».
- **CatalogModelLine + FilterSidebar**: фильтры/пагинация/заголовки — `t()`.
- **Мастер подбора (graph)**: UI-строки + вопросы узлов (`*_i18n` в `graph_json`,
  `QuestionGraph.save` синхронизирует ru) + опции/подсказки (`translate_wizard_content`).
- **TOP Menu + глобальный поиск**: перевод пунктов меню и строк поиска.

### НЕ сделано / остатки
- Тесты нового функционала не покрыты (только `core.tests.test_localization` — 11).
- `pa_controls` тест-сьют падает на миграции тестовой БД (pre-existing).
- Фразовый перевод медиа-имён неполный (коды/бренды остаются ru — осознанно).
- Всё некоммичено (HEAD=0e29325 «front en»): 34 modified + 9 untracked.
- Отладочный `print` в `SensorComponent.save()` — убрать.

---

## 12. Сессия 2026-10-07 (вечер) — spec_template_i18n остальных каталогов, шаблоны серий, тесты, Фаза 5, медиа-имена

### Сделано

1. **Отладочный print** в `SensorComponent.save()` — удалён (остаток §11).
2. **spec_template_i18n для остальных каталогов (задача 3 §9):**
   - Поля `spec_template_i18n` + sync ru в `_sync_localized_ru()`: `CableGlandModelLine`,
     `PneumaticActuatorModelLine`. Миграции `cable_glands/0021`, `pneumatic_actuators/0057`.
   - Команда `core/management/commands/translate_spec_templates.py` (идемпотентная):
     en/cn для 10 EquipmentType (ПП, позиционер для ПП, соленоиды, фитинги, дублёры, ФР, КВ,
     фитинг резьба-трубка, глушители, заглушки) + 8 серий КВ. БКВ не тронут.
   - Фикс `PneumaticActuatorModelLineItem._get_spec_sections(vars, locale=None)` (старая
     сигнатура) + новый `_get_spec_template_i18n()` (серия → EquipmentType).
   - Detail-вью 5 каталогов (КВ, соленоиды, редукторы, ФР, фитинги): локаль из
     `Accept-Language` в `to_dict(locale=...)` (паттерн БКВ).
3. **Шаблоны серий (§10 «НЕ сделано»):** команда
   `core/management/commands/translate_model_line_templates.py` (ключ — точный ru-шаблон,
   плейсхолдеры сохраняются): en/cn для 81 серии 8 каталогов (КВ, ПП, фитинги, соленоиды,
   БКВ, позиционеры, ФР, дублёры). Пилотные переводы БКВ не перезатёрты.
4. **Тесты нового функционала:** `core/tests/test_catalog_i18n.py` (12 тестов: spec-секции
   ru/en/cn, серия-синк, generate_name en/cn, detail-вью Accept-Language, идемпотентность
   команд). Прогон на копии боевой БД: `sqlite3.exe db.sqlite3 ".backup test_db.sqlite3"`,
   затем `manage.py test core.tests.test_catalog_i18n core.tests.test_localization --keepdb`
   → 23/23.
5. **Фаза 5 (прод-сборка + hash-fallback):** `npm run build` зелёный; через Django (8000)
   проверено в headless Chrome: SPA `/` (новый main-*.js), `/en/` (lang=en, меню EN),
   standalone `limit-switch-catalog` (секция + hash-режим `#?mode=quickselect`),
   standalone `posi-constructor`. `collectstatic --noinput` обновлён (420 файлов).
6. **Медиа-имена (задача «фразовый перевод неполный»):** расширен словарь
   `translate_media_names` (65+ фраз: листовки, РЭ, габаритные чертежи, позиционеры,
   фитинги/глушители/заглушки, откр/закр, общепром, и т.д.) + исправлен порядок
   («на пневмоприводы» до «пневмоприводы» и т.п.); переведено 295 строк.
   Остались только бренды/коды (Архимед, Север, ТР ТС, ЕАЭС, ГОСТ — осознанно).

### Осталось

- `staticfiles` содержит сиротские старые хэши — почистить `collectstatic --clear` (перед
  деплоем; в git уйдёт много удалений).
- `db.sqlite3` и `test_db.sqlite3` изменились (контент переводов).
- Полный тест-сьют pa_controls — pre-existing падение на тестовой БД (не чинился).

---

## 13. Сессия 2026-10-07 (ночь) — i18n UI-хрома всех каталогов (по отчёту пользователя)

### Проблема
Перевод «работал не везде»: пилот БКВ (limit-switch-catalog) переведён, остальные
каталоги — ru-хардкод в App.vue (labels-объект без t(), заголовки графов, eq-name,
хлебные крошки). Сравнение БКВ vs соленоидных — паттерн тот же, что в follow-up §3.

### Сделано
1. **Соленоидные клапаны**: ключи `sv.*` (18) в ru/en/cn; App.vue → computed(t()),
   total-label/eq-name/eqLabel.
2. **Остальные 7 каталогов** (gearbox `gb.*`, filter-regulator `fr.*`, cable-glands
   `cg.*`, pa `pa.*`, fittings `pf.*`, plugs `pp.*`, silencers `ps.*`): те же правки
   App.vue (labels computed + t(), graph total-label, AiSelectionPage labels.ai/eq-name/
   @navigate, eqLabel.value в breadcrumbs, pa: alerts + label фильтра «Конструкция»).
3. **Фикс доступа заглушки/глушители**: маршруты требуют meta.section catalog_plug /
   catalog_sil, а записей SiteSection не было (сплит 0015 их пропустил) → guard
   редиректил на /login. Data-миграция `project_customers/0018_add_plug_silencer_sections`
   создаёт разделы и выдаёт их ролям/клиентам, имеющим catalog_pf. /api/auth/me/ теперь
   отдаёт catalog_plug/catalog_sil.
4. `npm run build` зелёный; `collectstatic` обновлён (241 файл).

### Проверено
- grep: в App.vue всех 9 каталогов нет кириллических строковых литералов (кроме
  комментариев).
- Headless Chrome (vite, /en/): все 9 каталогов — EN-заголовки/подзаголовки/хлебные
  крошки; ранее заглушки/глушители показывали /login — теперь каталоги открываются.
- Тесты 23/23; `manage.py check` чисто.

### Осталось
- Некоммичено: i18n словари ×3, 8 App.vue каталогов, миграция project_customers/0018,
  staticfiles, db.sqlite3.
- Фаза 6 (паритет мини-приложений/SEO/QA) — отдельно.

---

## 14. Сессия 2026-10-07 (ночь, волна 2) — локализация карточек/фильтров всех каталогов (по отчётам пользователя)

### Проблемы (от пользователя, каталог Directional valves как образец)
1. CatalogModelLine: описание серии в заголовке без перевода.
2. Названия селекторов фильтров без перевода.
3. Карточки товара (ProductCard/SelectionResultGrid) с ru-текстом.

### Диагноз и фиксы (механизм общий, применён ко всем каталогам)
1. **to_dict-фоллбэк** (`core/models/catalog_serializer.py`): при отсутствии display_i18n
   name/description генерируются `generate_name(locale)`/`generate_description(locale)`
   из шаблонов серии (раньше — сырые ru-поля). Чинит карточки всех каталогов.
2. **list/engineer-вью 5 каталогов** (SV, gearbox, FR, fittings, CG): локаль из
   `Accept-Language` проброшена в `apply_filters_and_split(..., locale=locale)`.
3. **name_path для property/FK-листов** (`__name`-суффикс обязателен, иначе
   `_get_target_i18n` читает несуществующее поле):
   - SV: operation/construction/working_medium → `model_line__X__name`;
   - gearbox: gearbox_variety/gearbox_output_variety/stem_shape_*;
   - FR: filter_variety/protection_material;
   - CG: body_material_option__body_material, cable_types → model_line__cable_type__name.
4. **Property-резолверы → методы с locale + resolver в спецификации:**
   PF `swivel_display`, gearbox `is_declutchable_display` (снят @property).
5. **Фильтры:** `label_i18n` добавлен в ~50 FilterDefinition (SV 15, CG 17, FR 10,
   gearbox 9, fittings 11, documents 4).
6. **title/list_title EquipmentType** — команда `translate_et_title_templates`
   (en/cn для ET 3,4,7,10,11,12; ключ — точный ru-шаблон). Монтажные комплекты
   (ET 13-18) — fallback ru (каталоги-заглушки).
7. **Сериальный title КВ:** `CableGlandModelLine.title_template_i18n` (миграция
   cable_glands/0022) + sync/update_fields; `translate_model_line_templates` расширен
   на title_template (переводы == name_template); опечатка данных `{exd_short}}` вылечена.
8. **Справочники** (`translate_reference_dicts`): PneumaticConnection («Трубный монтаж»),
   MaterialSpecified (HNBR/FVMQ), StemShapes (Квадрат и др.), ActuatorGearboxOutputType
   (Четвертьоборотный и др.).
9. **Итоговый скан** engineer-эндпоинтов всех 9 каталогов (en): в карточках остались
   только бренды/коды (Архимед, КНК, ЯМАЛ/УРАЛ/АМУР, ГОСТ) — осознанная граница §2.

### Проверки
- Тесты: `core/tests/test_catalog_i18n.py` расширен до 16 (sections-эндпоинты всех
  каталогов + EN-поля карточек SV); 31/31 с test_localization.
- `manage.py check` / `makemigrations --check` чисто; `npm run build` зелёный;
  collectstatic обновлён; тестовая БД — свежий `.backup` боевой.
- lang.md: раздел 7 «Уроки первой волны» расширен до правил 11-17.

### Осталось (не в этой волне)
- Полная i18n админ-страниц (alert/label ru) — pre-existing.
- Монтажные комплекты ET 13-18 — title/list_title без en/cn (заглушки).
- Контент описаний серий фитингов/глушителей/заглушек (в БД пусто).
- `collectstatic --clear` перед деплоем; коммит (265 modified, 877 untracked).

---

## 15. Сессия 2026-10-08 — фитинги: выпрямление разновидности + раскол позиций/серий, фронт-каталог

### 1. Фронт: страница «Фитинги, заглушки» + иерархия
- Новая индексная страница `frontend/src/pages/catalog/CatalogFittingsPlugsIndex.vue`
  (маршрут `/catalogs/fittings-plugs`, ссылки на фитинги/глушители/заглушки).
- На `/catalogs/equipment` вместо «Фитинг резьба-трубка» — карточка «Фитинги, заглушки»
  (изображение фитинга).
- URL вложены: `/catalogs/fittings-plugs/pneumatic-{fittings,silencers,plugs}`
  + редиректы со старых `/catalog/pneumatic-*` (locale-aware `locRedirect`).
- Хлебные крошки трёх каталогов: Каталог → Фитинги, заглушки → [вид]. i18n ключи добавлены.

### 2. Вопрос 1: разновидность → форма + способ фиксации (в модели)
- Удалён `PneumaticFittingVariety` (junction shape+fixation+name) и FK `fitting_variety`;
  на `PneumaticFitting` добавлены прямые `shape`/`fixation_method`. Миграция `0024`
  (AddField + data-backfill из variety + замена `{fitting_variety}`→`{fixation_method} {shape}`
  в шаблонах + RemoveField + DeleteModel).
- Фильтры разделены: `fd_shape` + `fd_fixation_method` вместо `fd_fitting_variety`.

### 3. Вопрос 2: раскол позиций (одна модель → три)
- `AbstractPneumaticFitting` + `PneumaticFitting` / `PneumaticSilencer` / `PneumaticPlug`
  (у каждого свои FILTER_DEFINITIONS, config_hash_fields, NAME/VARS_FIELD_KEYS).
- Миграции `0025` (CreateModel ×2 + перенос строк по equipment_type + правка
  `source_content_type` SKU + RemoveField silencer-полей), `0026` (EquipmentType.content_type).
- config.py/views/admin/registry/handlers обновлены на три модели.

### 4. Раскол серий (по запросу пользователя)
- `AbstractPneumaticFittingModelLine` + `PneumaticFittingModelLine` (+ `shape`,
  `fixation_method`, `is_swivel`) / `PneumaticSilencerModelLine` / `PneumaticPlugModelLine`.
- Форма/способ фиксации перенесены С ПОЗИЦИИ НА СЕРИЮ фитингов; позиция наследует их
  через `model_line__shape`/`model_line__fixation_method` (реестр `pf_item_fields.py`).
- Миграция `0027`: CreateModel ×2 + перенос серий глушителей/заглушек + перепривязка
  `model_line` позиций + backfill shape/fixation на серии + RemoveField с позиций.
- Админка: в серии фитингов поля «Форма»/«Способ фиксации»; у позиции их больше нет.

### 5. Плейсхолдер `{equipment_type}`
- Добавлен в `PF_ITEM_TEMPLATE_FIELDS` и `NAME_FIELD_KEYS` трёх моделей (резолв
  `equipment_type__name`). Обновлены шаблоны EquipmentType глушителей/заглушек
  (`{model_code} {equipment_type} {brand}` — убраны фитинговые `{shape}`/`{fixation_method}`).

### 6. Прочее
- config_hash фитингов: добавлен `pipe_diameter` (иначе ~70 позиций с одинаковыми
  параметрами, но разным диаметром, давали коллизию хэша).
- Фронт: бейдж «Неактивно — спец. заказ» (красный, правый верх) на `ProductDetail.vue`
  при `is_active === false` (i18n ru/en/cn).
- Кабельные вводы: в боевой БД выставлено `is_active=False` для 324 позиций
  BLOCK + Латунь (проверка фильтрации по «активно»; обратимо).
- Ревью-фиксы: докстринги `KindCatalogConfig` удалены; словарь
  `translate_model_line_templates` обновлён (`{fitting_variety}`→`{fixation_method} {shape}`);
  dev-скрипты (`rename_all.py`, `fill_etp.py`, `_smoke_fixes.py`) покрывают три вида;
  `_COMMON_FILTER_DEFINITIONS` вынесена в модульную константу (без дублей).

### Проверки
- `manage.py check` — 0 проблем; миграции применены, `makemigrations --check` чисто.
- Каталоги: фитинги 128, глушители 25, заглушки 4 (200 OK); фильтры формы/способа работают.
- `generate_name()`: фитинг «…Цанговый (Push-in) Прямой…», глушитель «…Глушитель Camozzi…» — ок.
- Тесты `test_kind_catalogs` (9) и `test_fk_cascade` (10) — зелёные ПО ОТДЕЛЬНОСТИ.
  Совместный прогон двух модулей через `pneumatic_fittings/tests/settings.py` (копия боевой
  БД) падает на инфраструктуре (`Cannot operate on a closed database` + устаревшая копия) —
  pre-existing, не код.

### Осталось
- AI extract-промпты/схемы per-kind (`fitting-thread-pipe`/`fitting-silencer`/`fitting-plug`)
  — для требований с «своими параметрами» (сейчас только общий `pneumatic_fitting`).
- `npm run build` + `collectstatic --clear` перед деплоем; всё некоммичено.

---

## 16. Сессия 2026-10-09 — фитинги: перенос pressure/temp на серию + админ/плейсхолдеры/фильтры + переводы глушителей/заглушек

### 1. Перенос pressure/temp с позиции на серию
- `AbstractPneumaticFittingModelLine` — добавлены `pressure_min`/`pressure_max`/`temp_min`/`temp_max`.
- `AbstractPneumaticFitting` — эти 4 поля удалены; вместо них свойства-«отдаватели»:
  `pressure_min`, `temp_min`, `temp_max` (читают из `model_line`), `pressure_max_effective`
  (базово из серии), `_effective_pressure_max()`.
- `PneumaticSilencer` — оставлено поле `pressure_max` как **override**: `_effective_pressure_max()`
  возвращает фактическое значение, если оно не `None`/`0`, иначе значение серии.
- Проверка БД перед переносом: у фитингов/заглушек все 4 поля одинаковы внутри серии;
  у глушителей `pressure_max` различается (10 бар до 1/2", 6 бар у 3/4" и 1") → дефолт серии = мода (10),
  override = 6.

### 2. Миграции (разбиты на 3, чтобы не потерять данные)
- `0031` — AddField ×12 на серии + AlterField `pressure_max` глушителя (override).
- `0032` — data-миграция: серии получают значения из позиций; `pressure_max` серии = мода;
  у глушителей позиции-оверрайды (GAS-20, GAS-25, 2901 3/4", 2901 1") = 6, остальные NULL.
- `0033` — RemoveField pressure/temp с позиций (у глушителя `pressure_max` остаётся).
- Применены к боевой; `makemigrations --check` — чисто; имена позиций не затронуты
  (проверено: 157 позиций, 0 пустых имён).

### 3. Админка / плейсхолдеры / фильтры (по запросу пользователя)
- Админка серий: добавлены i18n-поля `description_i18n`, `name_template_i18n`,
  `description_template_i18n` (fieldset «Шаблоны названия и описания», паттерн FR/gearbox).
- Админка позиций: добавлены `weight` и `width_across_flats` (были на модели, не показывались).
- Плейсхолдеры: `pf_item_fields.py` — добавлены `{weight}`, `{width_across_flats}`;
  `pressure_max` путь → `pressure_max_effective`; ключи добавлены в NAME/VARS_FIELD_KEYS трёх видов.
- Фильтры: `temp_min` → `model_line__temp_min` (filters.py и catalog/filter_defs.py);
  добавлены `fd_pressure_min` (MAX/lte) и `fd_pressure_max` (MIN/gte); подключены в config.py.

### 4. Переводы i18n глушителей/заглушек
- `translate_model_line_templates.py`: в `MODELS` добавлены `PneumaticSilencerModelLine`
  и `PneumaticPlugModelLine` (раньше был только фитинг-серия); добавлены 3 недостающие
  словарные статьи (GA `name_template`, 2931 `name_template`, 2931 `description_template`).
- Команда запущена → переведено 10 полей (5 серий × name/description), «без перевода» — нет.
- Фикс FA-IOM-N: устаревший `{fitting_variety}` → `{fixation_method} {shape}` в сохранённом
  `name_template_i18n`/`description_template_i18n` (точечно, без `--force`, чтобы не затронуть
  97 серий по всем каталогам). Скан: неизвестных плейсхолдеров в *_template_i18n больше нет.

### Известные остатки (не этой сессии)
- Тест `test_series_of_other_kind_invisible` падает на пустой тестовой БД (id тестовой серии
  фитингов == id серии глушителя = 1 → коллизия) — pre-existing, не код. FK-cascade 10/10,
  kind-catalogs 8/9.
- `StructuredDataMixin._get_value` (строка `str(x) if x else ""`) перекрывает
  `TemplateMixin._get_value` → `pressure_min=0` в `template_vars` отдаётся пустой строкой
  (было и до переноса, не регресс; в названиях используется `pressure_range_display`).
- Серия S6512: RU-шаблон с `{brand}`, сохранённый перевод хардкодит «Camozzi» — вывод
  корректен, но перевод не «универсальный»; при желании добавить `{brand}`-вариант в словарь.

---

## 17. Сессия 2026-10-10 — EquipmentType: полные переводы шаблонов + i18n в редакторе

### Проблема (от пользователя)

В редакторе `/admin/pipeline-config` (EquipmentTypeEditor) видны только RU-шаблоны, а на
EN/CN-локалях фронт формирует названия карточек/заголовки по русским шаблонам. Запрос:
перевести шаблоны EquipmentType на JSON-i18n и в перспективе отказаться от шаблонов в сериях.

### Диагноз (проверено на боевой БД)

- Механика резолва исправна: `TemplateMixin._resolve_template` берёт перевод из `_i18n`
  **того же источника**, что и RU-шаблон (серия → EquipmentType → дефолт); приоритет
  серии сохраняется.
- Реальные пробелы были в данных EquipmentType: en/cn-переводы имели только title/list_title
  у части типов и полный набор у `lsb`. **40 полей** (20 × en/cn) не имели переводов:
  name/description/spec_title у ПП(3)/па-позиционера(4)/распределителей(7)/дублёров(10)/ФР(11);
  name/description у fittings(9)/КВ(12)/fitting-thread-pipe(17)/заглушек(25); все 5 полей у
  fitting-silencer(24); title/spec_title/list_title у монтажных комплектов mk-*(14–18).
- Видимо на сайте: ПП — 4 из 5 серий **без собственных шаблонов** (фолбэк на ET 3 → RU на en/cn);
  позиционеры/глушители прикрыты шаблонами серий (у серий переводы есть — 0 пропусков).
- API-причина «вижу только русские»: `EquipmentTypeListSerializer` (`ai_assistant/api/views.py`,
  эндпоинт `/api/ai-assistant/equipment-types/`, его использует редактор) не отдавал
  `*_i18n`-поля. Сам `EquipmentType` JSON-i18n-поля имеет с Фазы 4 (6 полей + sync_ru в save).

### Сделано

1. **`translate_et_title_templates` расширен** на все 5 текстовых шаблонов
   (name/description/title/spec_title/list_title; словарь `TEMPLATE_TRANSLATIONS`,
   ключ — точный ru-шаблон, плейсхолдеры сохраняются; идемпотентно). Запущен на боевой:
   переведено 40 полей, «без перевода» — нет. Покрытие i18n шаблонов EquipmentType — 100%.
2. **Сериализатор** `EquipmentTypeListSerializer` (ai_assistant/api/views.py): добавлены
   `name/description/title/spec_title/list_title_template_i18n` + `spec_template_i18n` —
   GET отдаёт, PATCH принимает (round-trip проверен тест-клиентом, 200).
3. **Редактор** `frontend/src/components/admin/EquipmentTypeEditor.vue`: переключатель
   локали RU/EN/CN на вкладках шаблонов (name/description/title/spec); EN/CN пишутся в
   `*_template_i18n` JSON, RU — в основное поле (синхронизируется в `_i18n.ru` на save);
   `SpecTemplateEditor` переключён на локаль (ru → `spec_template`, en/cn →
   `spec_template_i18n[locale]`); payload сохранения дополнен `_i18n`-полями.

### Проверки

- `manage.py check` чисто; тесты `test_localization` + `test_catalog_i18n` — 31/31 OK
  (после обновления копии `test_db.sqlite3` — фейл sections у заглушек был на устаревшей копии).
- `npm run build` зелёный.
- Смоук: `PneumaticActuatorCatalogItem` без серии → `generate_name('en')`/`generate_title('en')`
  отдают EN-шаблоны EquipmentType (раньше — RU); `/api/ai-assistant/equipment-types/` отдаёт
  6 `*_i18n`-полей с переводами.

### Осталось / решения на перспективу

- **Отказ от шаблонов в сериях** (запрос пользователя) — не делался: данные серий
  специфичны (GAS/2901 глушители и т.п.), механизм уже корректен. Для перехода нужно
  перенести уникальные шаблоны серий в EquipmentType (обобщить) и очистить поля серий —
  отдельная задача с ревизией данных; сейчас шаблоны серий просто имеют приоритет.
- `{equipment_type}`-плейсхолдер (глушители/заглушки) резолвится в `EquipmentType.name`,
  который **не локализован** (config-сущность, решение §2 п.9) → в EN-карточках может
  остаться слово «Глушитель пневматический». Кандидат: добавить `name_i18n`/`description_i18n`
  на EquipmentType (сейчас полей нет) — тогда резолв `equipment_type__name` локализуется
  через `_get_target_i18n` автоматически.
- Монтажные комплекты ET 14–18: переводы добавлены, но контента (карточек) почти нет.
- Не закоммичено: команда, views.py, EquipmentTypeEditor.vue, db.sqlite3 (+ весь
  некоммиченный хвост волн 1–2).

### Продолжение §17 (2026-10-10) — name_i18n/description_i18n на EquipmentType

По запросу пользователя: плейсхолдер `{equipment_type}` (глушители/заглушки) резолвился
в нелокализованный `EquipmentType.name`.

- **Модель** `core/models/equipment_type.py`: добавлены `name_i18n`/`description_i18n`
  (JSONField default=dict) + sync ru в `save()` (паттерн остальных `*_i18n`).
- **Миграция** `core/0025` — применена к боевой. `makemigrations --check` чисто.
- **Команда** `core/management/commands/translate_equipment_type_names.py` (идемпотентная):
  en/cn для 25 названий и 5 описаний ET. Запущена — покрытие 100%, пропусков нет.
- **Механика работает без правок mixins**: `_get_target_i18n('equipment_type__name')` и
  bare-FK `localized_name()` читают `name_i18n` автоматически.
- **Сериализатор** `EquipmentTypeListSerializer` (ai_assistant/api/views.py): добавлены
  `name_i18n`/`description_i18n` (GET/PATCH round-trip проверен).
- **Проверки:** глушитель GA-6 `generate_name('en')` = «…Pneumatic silencer Artorq…»,
  CN = «…气动消音器…» (раньше RU); 2901/заглушки — чисто; тесты 31/31; check чисто.

**Остаток в той же строке (не этой задачей):** значения `{filter_element}` (напр.
«сетчатый из спеченной бронзы») и `{shape}` («Конус») в EN-имени глушителя GA остаются
ru — справочники фитингов без en/cn. Кандидат на следующий шаг: расширить
`translate_reference_dicts`. Опечатка в данных: `mk-directional-valve-pa.description` —
текст про БКВ (копия с mk-lsb-pa).

### Продолжение §17 (2026-10-10, вторая часть) — админка переводов + защита ручных правок

По запросу пользователя (защита от перезаписи ручных правок и управление переводами
из админки):

1. **Админка — глобальный блок «Переводы (ru/en/cn)»** (`djangoProject1/admin_site.py`):
   патч `admin.ModelAdmin.get_fieldsets` — для любой модели с `*_i18n`-полями в конец
   формы добавляется свёрнутый (collapse) fieldset со всеми такими полями (исключён
   вычисляемый `display_i18n`). Покрывает 53 админ-класса и будущие модели автоматически.
2. **Виджет** `core/admin_widgets.py::PrettyJSONWidget` + статика
   `core/static/admin/{js,css}/i18n_json_field.*`: JSON с отступами (indent=2),
   моноширинный, на всю ширину, многострочный; кнопка «Форматировать» и подсветка
   валидности при потере фокуса. Подключается патчем `formfield_for_dbfield` ко ВСЕМ
   `*_i18n` JSONField (кроме display_i18n).
3. **Команды translate_* — защита ручных правок**: единая семантика «дозаполнять
   только отсутствующие локали; `--force` — перезаписать»:
   `translate_reference_dicts`, `translate_model_line_descriptions`,
   `translate_exd_climate_descriptions`, `translate_media_names`,
   `translate_material_texts` (data-fix AISl→AISI применяется всегда),
   `translate_sensor_electrical_specs`, `translate_signal_roles_and_sensors`,
   `translate_wizard_content`. (`translate_model_line_templates`/`translate_spec_templates`/
   новые ET-команды уже так работали.)

**Проверки:** check чисто; makemigrations --check чисто; тесты 31/31; рендер админки
SilencerShape и EquipmentType — блок «Переводы» есть, 2/8 textarea с виджетом, JS/CSS
подключены, JSON многострочный; эксперимент: ручная правка en выдерживает прогон
`translate_reference_dicts` (0 строк), `--force` возвращает словарь (171 строка).

**Замечания:** статику нужно `collectstatic` перед деплоем (в git — 3 новых файла).
В `translate_model_line_descriptions.py` в процессе правки была временная дубликация
класса — исправлена (ast-проверка пройдена).

### Ревью-фиксы §17 (2026-10-10, после review)

1. **F1 (дубли полей):** патч `get_fieldsets` теперь вычитает поля, уже показанные
   в собственных fieldsets админки (6 админок с дублями — серии фитингов/ФР/gearbox).
2. **F2:** защита `formfield is not None` в патче виджета.
3. **F3 (инлайны):** патчи перенесены на `BaseModelAdmin.formfield_for_dbfield` и
   `InlineModelAdmin.get_fieldsets` (импорт из `django.contrib.admin.options` — в Django
   5.2 `InlineModelAdmin`/`BaseModelAdmin` не экспортируются из `django.contrib.admin`).
4. **F4:** `EquipmentType.save()` — пустое описание не пишет `'ru': ''`, а чистит
   устаревший ru-ключ.
5. **F5 (тесты):** `core/tests/test_catalog_i18n.py` +4 теста
   (`TranslateCommandFillMissingTests`, `AdminI18nFieldsetTests`) — 35/35.

**Итог дня (2026-10-10):** check/makemigrations --check чисто; тесты 35/35;
`npm run build` зелёный. Всё некоммичено (плюс хвост волн 1–2); перед деплоем —
`collectstatic` (3 новых статических файла).



