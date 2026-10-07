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

---

## 7. Уроки первой волны (2026-10-07, после перевода всех каталогов)

### Фронт-каталоги (App.vue мини-приложений)

1. **Ключи словарей — только латиницей, в неймспейсах** (`catalog.*`, `lsb.*`, `sv.*`,
   `gb.*`, `fr.*`, `cg.*`, `pa.*`, `pf.*`, `pp.*`, `ps.*`, `menu.*`, `search.*`).
   Антипаттерн: `t('Русская строка')` — «ключ = ru-текст» с переводами в en/cn под
   кириллическим ключом. Так ru работает только за счёт fallback-на-ключ, а словари
   засоряются кириллицей. Правильно: `t('menu.customers')`; ru-текст — значение в ru.js.
2. **`labels` каталога — только `computed(() => ({...}))` на `t()`-ключах.** Plain-объект
   с ru-строками не перерисуется при смене локали (это была причина «перевод не везде
   работает»).
3. **Хлебные крошки:** `eqLabel = computed(() => t('<app>.breadcrumb'))`, в `breadcrumbs`
   использовать `eqLabel.value` (computed в script не разворачивается сам).
4. **Прочие хардкоды в шаблоне:** `:total-label` графа → `t('catalog.common.foundLower')`;
   `AiSelectionPage` → `:labels="labels.ai"` + `:eq-name="t('<app>.eqName')"` + `@navigate`;
   alert'ы/подписи фильтров — тоже через `t()` (`t(key, {param})` поддерживает `{param}`).
5. **Проверка:** в App.vue не должно остаться строковых литералов с кириллицей
   (grep `['"][А-Яа-яЁё]`); в en.js/cn.js — кириллических имён ключей.
6. **Новый каталог = доступ:** помимо маршрута с `meta.section` нужна запись `SiteSection`
   с тем же code + регистрация codename в `object_registry` (`section_code=...`) + права в
   `SystemGroup` (anonymous_users/authenticated_users). Иначе guard фронта редиректит на
   /login даже при AllowAny-вьюхах (было с заглушками/глушителями: сплит 0015 их пропустил,
   чинится data-миграцией).

### Команды-переводчики контента (translate_*)

7. **Ключ словаря — точная ru-строка** (шаблон/описание/подпись). Порядок замен важен:
   более длинные фразы раньше коротких (иначе «на пневмоприводы» съест «пневмоприводы»
   раньше и оставит сироту «на»).
8. **Короткие подстановки («РЭ», «ДС», «ИЛИ», « и », « от ») — только если полные фразы
   не покрывают.** Скан имён на ложные совпадения перед запуском; новые имена могут
   сломать. Предпочтительны многословные фразы.
9. **`--force` — merge-семантика, не перезапись:** подписи/группы, которых нет в словаре,
   сохраняют существующий перевод (позиционно), иначе — fallback ru. Иначе команда
   затирает ручные переводы каталогов, не покрытых словарём (кейс БКВ в
   `translate_spec_templates`).

### Бэкенд: sync-контракт `_i18n` (§8 SESSION.md — дополнение)

10. Модель с собственным `_i18n`-полем обязана не только переопределить
    `_sync_localized_ru()`, но и добавить поле в `update_fields` при partial-save:
    ```python
    def save(self, *args, **kwargs):
        if kwargs.get('update_fields') is not None:
            kwargs['update_fields'] = set(kwargs['update_fields']) | {'spec_template_i18n'}
        super().save(*args, **kwargs)
    ```
    Иначе `save(update_fields=['name'])` рассинхронизирует ru-копию нового поля
    (миксины добавляют только свои три поля).

11. **Описания серий в CatalogSection локализуются только через `sections/`-эндпоинт.**
    Без него фронт делает fallback `list({limit: 1000})`, который отдаёт сырое ru-описание.
    У каждого каталога должен быть `GET .../sections/` (образец —
    `pa_controls/views/catalog.py::LimitSwitchBoxSectionView`): серии с активными айтемами
    (`related_name` items → Count), первое фото, бренд и
    `pick_i18n(description_i18n, locale, fallback=description)`; локаль — из
    `Accept-Language`. Фронт: `ENDPOINTS.<app>.sections` + `getSections()` в api.js.
    Для каталогов с видами (фитинги/глушители/заглушки над одной моделью) — один view
    с `kind_code` (`model_line__equipment_type__code`) и три URL.

12. **Карточки товара (списки/подбор/деталка) локализуются в `CatalogSerializerMixin.to_dict`.** Если у модели нет `display_i18n` (только пилот БКВ), name/description должны
    генерироваться `generate_name(locale)`/`generate_description(locale)` из шаблонов
    серии, а не отдаваться сырые ru-поля. `to_values_dict` (карточки SelectionResultGrid)
    получает локализацию через тот же `to_dict`. `title`/`list_title` — из
    `title_template_i18n`/`list_title_template_i18n` EquipmentType (команда
    `translate_et_title_templates`).
13. **Значения-справочники внутри шаблонов.** Если item-плейсхолдер резолвится через
    `@property`-строку (не FK) — задать в реестре полей `name_path='model_line__X__name'`:
    тогда `_resolve_data_dict_target` читает `name_i18n` справочника. Сам справочник должен
    иметь перевод (команда `translate_reference_dicts`, ключ — ru-строка).
14. **Подписи фильтров каталога** — `label_i18n` в FilterDefinition (en/cn), иначе метки
    останутся ru даже при локализованных опциях. Опции локализуются автоматически
    (`get_options(locale)` → `localized_name`) при условии переводов справочников.

15. **FK-лист без `__name` в `name_path` не локализуется.** `_get_target_i18n('model_line__X')`
    читает `X_i18n` у серии (его нет) → fallback ru. Всегда: `name_path` (и `path` для
    имени) заканчивать на `__name` для FK-листов (`'model_line__filter_variety__name'`).
16. **Property-резолверы ru-строк** (`@property` возвращает ru-текст) — превращать в метод
    `def x(self, locale=None)` + в спецификации добавить `'resolver': 'x'` (path оставить
    для display). `_call_resolver` передаёт локаль, если метод её принимает.
17. **Модельные серии с собственным `title_template`** (напр. КВ): добавить
    `title_template_i18n` (+sync, +update_fields) и переводить той же командой
    (`translate_model_line_templates`; переводы title == name, ключ — точная ru-строка;
    опечатки в данных вроде `{exd_short}}` ломают exact-match — чинить данные).
