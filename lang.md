# Локализация (RU/EN/CN) — общий паттерн и чек-лист

Единый подход для локализации моделей/справочников/текстов. Локали: `ru` (базовый),
`en`, `cn` (код везде `cn`; `Accept-Language: zh*` → `cn`).

Ядро: `core/utils/localization.py` — `pick_i18n`, `sync_ru`, `set_locale`,
`localized_name`, `locale_from_accept_language`, `localize_service_word`.

---

## 1. Хранение: `<field>_i18n` (общий паттерн)

Базовое RU-поле остаётся рабочим (редактируется как раньше). Рядом — JSONField:

```python
description = models.TextField(blank=True, ...)          # RU
description_i18n = models.JSONField(default=dict, blank=True)  # {"ru","en","cn"}
```

- Миксины (для name/description справочников): `LocalizedDictFieldsMixin`
  (name+description), `LocalizedNameFieldsMixin` (только name),
  `LocalizedDescriptionFieldsMixin` (только description), `LocalizedModelLineMixin`
  (description + шаблоны серии).
- **Синхронизация ru на save**: миксины делают `_sync_localized_ru()` (переопределить
  и добавить свои поля, если нужно). `sync_ru(i18n, ru)` возвращает новый dict с
  обновлённым `ru` (en/cn не затирает).
- Частичные `save(update_fields=[...])` без `_i18n`-полей рассинхронизируют ru —
  миксины добавляют свои `_i18n` в `update_fields`; массовые `.update()` — только
  если знаешь, что делаешь.

## 2. Чтение: локаль → значение

- `pick_i18n(field_i18n, locale, fallback=ru_value)` — для строковых полей.
- `localized_name(obj, locale)` — для имени справочника (читает `obj.name_i18n`).
- Локаль из запроса: `locale_from_accept_language(request.headers.get('Accept-Language'))`.

## 3. Что переводить / что НЕ переводить

**Переводится:** описательные названия, описания, шаблоны, подписи, вопросы,
подсказки, свободные тексты.

**НЕ переводится (fallback ru):** коды (`code`/`symbolic_code`/FK-коды), торговые
названия серий, аббревиатуры (`Ex d`, `IIA`, `T1`, `SPDT`, `NAMUR`, `IP67`), бренды.

## 4. Чек-лист при локализации новой модели

1. **Модель** — подключить миксин (`Localized*FieldsMixin`) или добавить
   `field_i18n` + переопределить `_sync_localized_ru()`. `makemigrations` +
   `migrate`.
2. **Сериализатор/вью** — прочитать локаль и пробросить её; отдавать
   `pick_i18n(...)`/`localized_name(...)` вместо сырого поля. У резолверов —
   добавить `locale=None` (резолверы вызываются через `_call_resolver`/`_resolve_field`/
   `_resolve_data_dict_target`, которые передают локаль, если метод её принимает).
3. **Шаблоны** (`name_template`/`description_template`/`spec_template`) — для
   локализуемых текстов добавить `<field>_template_i18n` (JSON) и читать через
   `pick_i18n` в `_resolve_template` / `_get_spec_sections`.
4. **Фронт** — UI-строки через `t()` + ключи в `frontend/src/shared/i18n/locales/{ru,en,cn}.js`.
   `api.js` уже шлёт `Accept-Language`. Для `<a href>`-скачиваний добавлять `?lang=`
   (браузерный переход не шлёт наш `Accept-Language`).
5. **Контент (en/cn)** — идемпотентная management-команда (keyed by `code`/ru-строке),
   заполняет `*_i18n['en'/'cn']`. Фразовый/словарный перевод; коды не трогать.
6. **Единицы/служебные слова** — `localize_service_word` (подстановки единиц «°С»→«°C»,
   «кг»→«kg», «В»→«V», «Гц»→«Hz», «до»→«up to» и т.п.).

## 5. Проверка

- `python manage.py check`
- `python manage.py makemigrations --check --dry-run` (нет незакоммиченных миграций)
- `python manage.py test core.tests.test_localization --keepdb`
- Smoke через `django.test.Client`: `GET ... HTTP_ACCEPT_LANGUAGE='en'` → en-значения;
  без заголовка → ru; `zh-CN` → cn.
- `cd frontend && npm run build`

## 6. Готовые примеры в репо

- Справочники: `params/models.py`, `pa_controls/models/pa_control_options.py`.
- Серии: `pa_controls/models/lsb_model_line.py` (`LocalizedModelLineMixin`).
- Шаблоны/данные датчика: `pa_controls/models/sensor.py` (`get_exi_params`,
  `get_electrical_specs`, `extra_params`), `pa_controls/models/limit_switch.py`
  (резолверы сигналов).
- Спецификация `.docx`: `core/models/spec_docx.py`, `core/spec_doc_views.py`.
- Фильтры/каскады: `core/climate_views.py`, `core/views.py` (Exd), `params/exd_models.py`.
- Мастер подбора: `core/question_graph_views.py` (узлы + опции).
- Медиа/сертификаты: `media_library/models.py`, `cert_doc/models.py`,
  `core/models/catalog_serializer.py` (`_get_certs_section`/`_build_doc_dict`).
- Команды-переводчики: `core/management/commands/translate_*.py`.
