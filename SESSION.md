# SESSION.md — актуальные задачи и соглашения (обновлено 2026-10-13)

Назначение: только **незавершённые дела** (проверены на актуальность 2026-10-13) и
**соглашения/паттерны** разработки. История завершённых работ не хранится.

---

## 1. Соглашения и паттерны (единый блок)

### 1.1 Локализация RU/EN/CN
- Локали: `ru` (базовый), `en`, `cn`. Код везде `cn`; `Accept-Language: zh*` → `cn`;
  URL-префиксы фронта `/en/`, `/cn/`. Полный чек-лист и правила — **`lang.md`** (главный
  документ по локализации новых моделей).
- Хранение: базовое RU-поле остаётся рабочим; рядом `<field>_i18n` = JSON `{"ru","en","cn"}`;
  ru синхронизируется в `_i18n["ru"]` при полном `save()`; чтение — `pick_i18n`/`localized_name`.
- НЕ локализуются: коды (`code`/`symbolic_code`/FK-коды), торговые названия серий, бренды,
  аббревиатуры (Ex d, IP67, NAMUR, Т1–Т6 и т.п.).
- Локаль данных — заголовок `Accept-Language`; gettext-хром (`?lang=`) — для скачиваний.
- Переводы контента — идемпотентные команды `core/management/commands/translate_*.py`
  (ключ — точная ru-строка; заполняют только отсутствующие локали; `--force` — перезапись;
  порядок замен — длинные фразы раньше коротких).

### 1.2 Архитектура каталогов (общий паттерн)
- Шаблоны резолвятся на 2 уровнях: `model_line` → `EquipmentType` (фоллбэк); переводы
  `*_template_i18n` читаются из ТОГО ЖЕ источника, что и RU-шаблон.
- Item-модели: `TemplateMixin` (generate_name/description/title/spec_title/list_title,
  `_fill_template`, `skip_auto_generate=True` пропускает генерацию в `save()`),
  реестр полей `*_item_fields.py` (path/name_path/resolver/code_path/ext_code_path),
  списки ключей NAME/CODE/VARS_FIELD_KEYS; спецификация — `spec_template` (EquipmentType
  или серия) + `spec_template_i18n` (локаль внешним ключом).
- `CatalogSerializerMixin.to_dict(locale=None)` — карточки локализуются в нём; резолверы
  принимают `locale` (вызываются через `_call_resolver`/`_resolve_data_dict_target`).
- Фронт: UI-хром через `t()` + ключи латиницей в неймспейсах (`catalog.*`, `<app>.*`);
  `labels` каталога — только `computed(() => ({...}))`; `useCatalogRoute` отдаёт id из URL
  строкой → пропы id объявлять `[Number, String]` и нормализовать `Number()` при использовании.
- Плейсхолдеры `{torque_6bar}`/`{torque_table}` (ПП) — резолверы в `pa_item.py`, правила
  таблицы моментов — в `pa_torque.py` (`_get_torque_fields_for_construction`).

### 1.3 Карточки ПП (PneumaticActuatorCatalogItem)
- 5999 карточек материализованы из типоразмеров × through-опций; `exclude_from_catalog=True`
  (не в листингах, есть в глобальном поиске/деталке); браузинг — страница `pa-catalog-browse`.
- `config_hash` = каноническая конфигурация (опции; ext-кодировка в хэш НЕ входит);
  `generate_pa_cards` — идемпотентный дифф по хэшу: создаёт новые, обновляет при расхождении
  code/name/description (сравнение на existing с загруженными связями), `--archive` —
  деактивирует исчезнувшие, `--dry-run` — без записи; ручные карточки (`origin=manual`)
  не трогаются. Прогресс-лог каждые 100 записей.
- Артикул = render(`model_item_code_template`) + « » + render(`ext_encoding_template`);
  генераторы артикула чистят пустые скобки `()` и артефакты `-.`/`.-`.
- Регламент: после изменения опций/типоразмеров/шаблонов — повторный прогон
  (+ `--archive` при удалении комбинаций).

### 1.4 Тестовая БД и тесты
- Тесты — на копии боевой БД `test_db.sqlite3` (создание: `sqlite3.exe db.sqlite3 ".backup test_db.sqlite3"`);
  запуск — `python manage.py test <модули> --keepdb` (без `--keepdb` копия уничтожается).
- Только `TestCase` (транзакционные); `TransactionTestCase` чистит таблицы копии.
- Штатные проверки: `manage.py check`, `makemigrations --check`, `npm run build`.

### 1.5 Права доступа (object_registry / SystemGroup)
- `OBJECT_REGISTRY` (core/object_registry.py) — канонический список системных объектов
  (страницы/конфигураторы/каталоги/админ-страницы) в коде; заполняется модулями
  `<app>/object_registry.py` при старте. БД хранит только права
  (`SystemGroup.object_permissions` = {codename: [view/manage]}).
- `post_migrate` автосинк: administrators — `manage` на все объекты; anonymous_users —
  `view` на `type in ('catalog','configurator')`; устаревшие codename'ы вычищаются.
- Новый каталог = запись в реестре (codename `catalog.<x>`, `section_code`) + `SiteSection`
  с тем же code + права группам + `meta.section` на маршруте фронта. Иначе guard редиректит
  на /login (кейс глушителей/заглушек, SESSION-история 2026-10-07).

### 1.6 Прочие конвенции
- GraphQL заморожен — только REST (DRF); SSR (Nuxt) на паузе — SPA.
- Константы вместо магических строк: код шестерни-рейки — только
  `ACTUATOR_VARIETY_RP_DEFAULT_CODE` ('RP'; данные в БД приведены к 'RP').
- `db.sqlite3` (боевая) остаётся в git; `test_db.sqlite3` — вне git.
- Резолверы с текстом, зависящим от локали — методы `def x(self, locale=None)`.

---

## 2. Незавершённые дела (актуально на 2026-10-13)

### A. Перегенерация карточек ПП — СДЕЛАНО (2026-10-13)
- Прогон `generate_pa_cards` завершён: все 5999 карточек синхронизированы (контрольный
  прогон — «обновлено=0»); 0 пустых имён, 0 дублей кодов, 0 артефактов «()».
- Команда оптимизирована: один запрос всех карточек, сравнение на existing,
  батч-транзакции по 100 + update_fields, прогресс-лог каждые 100; полный проход ~2–3 мин.
- Осталось от этой задачи: проверить одну цену (PriceDocument/PriceHistory) на SKU;
  решить про CTA «открыть в конфигураторе» с initialOptions (pa_card_pattern.md).

### B. Through-опции: паттерн ПП на остальные каталоги + чистка схемы
1. **Перенести ЭП/КВ/позиционеры/распределители на паттерн ПП**: reference-опции →
   `_localized_base_name()` из справочника; по их каталогам не смоук-тестировано
   (делегирование свободной функции сейчас глобально добавляет суффикс + service-word).
2. **Удалить `name_i18n` из схемы `BaseThroughOptionNoDefault`** (у ПП поле пустое,
   `translate_pa_option_names` — no-op). Требует миграций 6 приложений.
3. **ЭП:** `ElectricBodyCoatingOption.body_coating` CharField → JSON (значения те же, что
   были у ПП) + `_res_body_coating`-аналог; **SKU ЭП** (не трогалось).
4. **Позиционеры:** `PosiSignalProfileOption.name` → name_i18n/JSON.
5. **Общий `description` через-моделей** (TextField) → description_i18n (отдаётся в
   get_option_info/конструкторе).

### C. Дубли в селекте «Взрывозащита» (инженерный подбор ПП)
`PneumaticExdOption` без поля `code` (есть `encoding`): ids 6/11 и 8/9 отображаются
одинаково («Общепромышленное (Стандарт)», «Ex db / Ex tb (Стандарт)»), но фильтруют разные
подмножества. Решение: показывать `encoding` в label селекта или группировать по имени.
НЕ дедуплицировать по имени — семантика разная.

### D. ext-артикулы (ext_encoding) для остальных
`ext_encoding_template` + реестр `ext_code_path` сделаны для ПП и ЭП. По паттерну —
**CG / позиционеры / распределители** при необходимости (данные ext_encoding заполняет
пользователь).

### E. Каталоги-заглушки → реальные страницы (запланировано пользователем)
Позиционеры, шкафы управления ЭП, монтажные комплекты. При создании страниц:
`SiteSection` + права группам + `meta.section` на маршруте + запись в реестре
(`catalog.positioners` уже добавлен в `pa_controls/object_registry.py`; для шкафов/монтажных
записей пока нет — моделей нет). `catalog.ea_reducers` в реестре есть, но страница — заглушка.

### F. AI extract-промпты per-kind для фитингов/глушителей/заглушек
Только общий `pneumatic_fitting`; нужны `fitting-thread-pipe`/`fitting-silencer`/`fitting-plug`
(для требований со «своими» параметрами). Проверено 2026-10-13: промптов per-kind нет.

### G. Данные (заполняет пользователь)
1. **Таблица моментов:** у PA1000 нет строк при 6 бар для пружин 06/07 (плейсхолдер
   `{torque_6bar}` отдаёт только SPR-часть); у RT032 (body 80) нет SR-строк моментов.
2. **Переводы справочников:** значения `{filter_element}` глушителей («сетчатый из спеченной
   бронзы») — ru в EN/CN-именах (SilencerShape и MaterialSpecified переведены 2026-10-13;
   у MaterialSpecified без en остались только латинские EPDM/NBR/PTFE/FEP/PFA/Viton —
   перевод не нужен).
3. Описания серий: 1 пустое у фитингов, 2 у глушителей.
4. Мелочи: серия S6512 — сохранённый перевод хардкодит «Camozzi» вместо `{brand}`;
   монтажные комплекты ET 14–18 — контента (карточек) почти нет.

### H. Технический долг
1. **Pre-existing падения тестов:** полный сьют pa_controls на тестовой БД
   (`test_question_graph_options`, `test_wizard` — ожидают пустую БД/несуществующее поле);
   `test_series_of_other_kind_invisible` — коллизия id на пустой БД. Перепроверить при
   следующем полном прогоне.
2. **`StructuredDataMixin._get_value`** перекрывает `TemplateMixin._get_value` →
   `pressure_min=0` в `template_vars` отдаётся пустой строкой (не регресс, но некрасиво).
3. **WARNING «Плейсхолдер {hand_wheel} не найден»** при генерации имён части серий ПП
   (fallback работает; косметика).
4. **Полная i18n админ-страниц** (alert/label ru) — pre-existing.
5. **N+1 в общем сериализаторе** (~64 запроса/карточку: M2M exd, галерея, монтаж/присоединения) —
   на SQLite некритично, отдельная оптимизация.
6. **`collectstatic --clear`** перед деплоем (сиротские старые хэши в staticfiles).
7. **Фаза 6:** паритет мини-приложений/SEO/QA — отдельно.
8. **Отказ от шаблонов в сериях** (перспектива, запрос пользователя): перенести уникальные
   шаблоны серий в EquipmentType и очистить поля серий — отдельная задача с ревизией данных.
9. **P8:** после переноса through-опций с legacy item — убрать мостик `source_model_line_item`
   и упростить `_iter_combos`.
10. **БКВ:** «или» в `cable_glands_holes_list_text`/`mounting_list_text` (lsb_body.py) —
    хардкод, не локализуется.

### I. Некоммичено (2026-10-13)
- Код: `generate_pa_cards.py` (оптимизация+лог), `pa_item.py`/`pa_item_fields.py`
  (`{torque_6bar}`), `PaActuatorConfigurator.vue` (пропы id), `test_catalog_i18n.py`,
  `HomePage.vue`, `Site-design-description.docx`, `tasks-2026-10-13.txt`.
- Новое: `pa_controls/object_registry.py` (catalog.positioners).
- Данные: `db.sqlite3` (код конструкции 'RACK-PINION'→'RP', частично обновлённые карточки).
- Внимание: в рабочей папке есть `db.sqlite3-journal` (хвост убитого процесса) и
  `~WRL0003.tmp`/`~$te-design-description.docx` (временные Word) — не коммитить.
