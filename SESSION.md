# Состояние проекта на 2026-05-25

## Ключевые архитектурные решения

1. CatalogDictMixin в core/models/mixins.py — единый to_dict() для всех каталогов
2. to_dict() → sections (gallery/specs/docs/certs/description) + template_vars
3. _get_template_vars() — единый источник значений. _get_data_dict() — для TemplateMixin
4. Цены вшиты в ответ API, конвертация через ExchangeRate, валюта из CustomerSettings
5. CSS Custom Properties — default/dark/minimal темы, компоненты ссылаются на переменные
6. Виджет widget/ — клиентский hash-роутер (#/gearbox/detail/123), F5 работает
7. Shared-компоненты — переиспользуются для всех типов каталогов
8. Фильтры списка: scope=used (только существующие), формы создания: scope=all (полные справочники)

## Правила работы
- Не писать в существующие файлы без разрешения
- Шаг за шагом
- При смене машины читать SESSION.md (в git)

## Реализованные каталоги

### Редукторы (gearbox)
- **Бэкенд**: GearBox(CatalogDictMixin, SKUMixin, ...), to_dict() + to_values_dict(), фильтры, цены
- **Фронтенд**: frontend/src/apps/gearbox-catalog/ (4 страницы)
- **API**: /api/gearbox/catalog/, /<id>/, /filters/, /meta/

### Фильтр-регуляторы (filter_regulator)
- **Бэкенд**: FilterRegulator(CatalogDictMixin, TemplateMixin, ...)
  - FilterRegulatorModelLine(CertDocMixin, ...) — сертификаты через model_line
  - to_dict(): 5 секций (Images, Specs 4 группы, Docs, Certs, Description)
  - Фильтры: model_line_id, filtration_rating_min, body_material_id, flow_rate_min, thread_id, work_temp_min/max, brand_id
  - Инженерный каталог: /api/filter-regulator/engineer/
- **Фронтенд**: frontend/src/apps/filter-regulator-catalog/ (5 страниц + EngineerCatalog)
- **Инженерный каталог**: чипсы серий и фильтров, авто-дефолты, одна карточка через ProductDetail
- **API**: /api/filter-regulator/catalog/, /<id>/, /filters/, /meta/, /engineer/
- **Виджет**: CatalogIndex «Фильтр-регуляторы», маршруты #/filter_regulator/*
- **Меню**: TopMenu «⚙️ Настройки» → «🔧 Фильтр-регуляторы», «🔬 Инженерный каталог»

### Блоки концевых выключателей (pa_controls)
- **Бэкенд**: LimitSwitchBox(CatalogDictMixin, TemplateMixin, SKUMixin, ...)
  - _get_template_vars(): 25 строковых значений
  - to_dict(): 5 секций (Images, Specs 4 группы, Docs, Certs, Description)
  - to_values_dict(): облегчённая для списков
  - Секции specs: Основные (9 полей), Корпус (5), Датчики (4), Условия эксплуатации (1)
  - Фильтры: model_line_id, sensor_variety_id, points, ip_id, work_temp_min/max, body_material_id, model_line_brand_id, signal_type_id, exd_id

## Фильтрация: scope=used / scope=all
- Медиатека: MediaFilterOptionsView — ?scope=used / ?scope=all
- Сертификаты: CertFilterOptionsView — ?scope=used / ?scope=all

## Исправления
- [x] Замена файла в медиатеке — мгновенное обновление DOM (без location.reload)
- [x] Копирование в медиатеке — логика в модели MediaLibraryItem.copy()
- [x] Сертификаты в filter-regulator — _get_certs_section()
- [x] Фильтр по серии (model_line_id) вместо brand_id в filter-regulator
- [x] Инженерный каталог фильтр-регуляторов
- [x] LimitSwitchBox — переписан на CatalogDictMixin

## Важные пути

| Ресурс | Путь |
|--------|------|
| CatalogDictMixin | core/models/mixins.py |
| GearBox.to_dict() | gearbox/models/gearbox.py |
| FilterRegulator.to_dict() | filter_regulator/models/fr_model_line_item.py |
| LimitSwitchBox.to_dict() | pa_controls/models/limit_switch.py |
| FilterRegulator фильтры | filter_regulator/services/filters.py |
| Инженерный каталог (бэкенд) | filter_regulator/views/engineer.py |
| Инженерный каталог (фронтенд) | frontend/src/apps/filter-regulator-catalog/components/EngineerCatalog.vue |
| Shared компоненты | frontend/src/shared/components/ |
| CSS темы | frontend/src/shared/themes/ |
| Виджет | frontend/src/apps/widget/ |
| WordPress плагин | wp-catalog-plugin/catalog.php |
| Vite config | frontend/vite.config.js |
| Главный urls.py | djangoProject1/urls.py |
| Цены / валюта | price/services/currency_converter.py |
| Медиатека (админ) | media_library/admin.py |
| Медиатека (модель) | media_library/models.py |
| Сертификаты (фильтры) | cert_doc/views/filters.py |
