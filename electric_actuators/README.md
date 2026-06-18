# electric_actuators — Электроприводы

Приложение Django для каталога и конфигуратора электроприводов.

> Обновлено 2026-06-18: ControlUnitWiring, рефакторинг ElectricControlUnitOption, фронтенд-админки

## Архитектура

```
electric_actuators/
├── models/
│   ├── ea_model_line.py              # ElectricActuatorModelLine — серия (ABRA-BUV-VF826)
│   ├── ea_model_line_item.py         # ElectricActuatorModelLineItem — модель в серии (DN100)
│   ├── ea_model_line_item_options.py # Through-опции уровня model_line_item
│   ├── ea_options.py                 # Through-опции уровня model_line
│   ├── ea_allowed_options.py         # Allowed*Option (кодировки опций для серии)
│   ├── ea_control_unit_wiring.py     # ControlUnitWiring — справочник БУ+напряжение+профиль+схема
│   ├── ea_model_body.py              # ModelBody — корпус привода
│   ├── ea_body.py                    # ElectricActuatorBody — таблица корпусов
│   ├── ea_cg_holes_set.py            # CableGlandHolesSet — наборы кабельных вводов
│   ├── ea_actuator_constructor.py    # Конструктор (пошаговый подбор)
│   ├── ea_actuator_selected.py       # Выбранная конфигурация (сохранённый подбор)
│   ├── ea_data.py                    # ElectricActuatorData — технические данные
│   └── ea_wiring_diagram.py          # WiringDiagram — заглушка (закомментирована)
├── admin/                            # Админки (по файлу на модель)
├── api/                              # REST API
│   ├── views_admin.py                # EAPowerSupplyMatrix (матрица напряжений)
│   └── views_admin_items.py          # Админка model_line_item + ControlUnitWiring CRUD
├── services/                         # Бизнес-логика
├── graphql/                          # GraphQL схема
├── static/                           # Статика
└── templates/                        # Шаблоны
```

## Ключевые модели

### Серия и модель

| Модель | Назначение |
|--------|-----------|
| `ElectricActuatorModelLine` | Серия электроприводов (ABRA, FAF, NK…) — общие свойства и опции |
| `ElectricActuatorModelLineItem` | Модель в серии (DN100, DN150…) — размер, момент, мотор |

### Through-модели опций

Опции привязываются через through-модели, которые хранят `encoding`, `is_default`, `sorting_order`.

**Уровень model_line** (едины для всех DN и напряжений):
- `ElectricTemperatureOption` — климатическое исполнение
- `ElectricIpOption` — степень защиты IP
- `ElectricExdOption` — взрывозащита
- `ElectricBodyCoatingOption` — покрытие корпуса
- `ElectricBodyColorOption` — цвет корпуса
- `ElectricHandWheelOption` — ручной дублёр
- `ElectricTurnAngleOption` — угол поворота
- `ElectricBlinkerOption` — блинкер
- `ElectricMechanicalIndicatorOption` — мех. индикатор
- `CableGlandHolesSetBodyOption` — набор кабельных вводов

**Уровень model_line_item** (вариативны по напряжению):
- `ElectricPowerSupplyOption` — напряжение + моторные параметры (ток, мощность, время, момент)
- `ElectricSafetyPositionOption` — положение безопасности
- `ElectricControlUnitOption` — блок управления + счётчики + схема подключения
- `ElectricEndSwitchesOption` — концевые выключатели
- `ElectricWaySwitchesOption` — путевые выключатели
- `ElectricTorqueSwitchesOption` — моментные выключатели

### ControlUnitWiring (добавлен 2026-06-18)

Справочник связок: БУ + напряжение + профиль сигналов + изображение схемы.

| Поле | Тип | Назначение |
|------|-----|-----------|
| `control_unit` | FK → ControlUnitInstalledOption | Тип БУ |
| `power_supply` | FK → PowerSupplies | Напряжение питания |
| `signal_profile` | FK → ControlUnitSignalProfile | Профиль сигналов |
| `wiring_diagram` | FK → MediaLibraryItem | Изображение схемы (категория SCHEMA) |
| `name` | CharField(200) | Название схемы |
| `code` | CharField(50, unique) | Уникальный код |
| `description` | TextField | Описание |
| `cached_json` | JSONField | Предсобранные данные для быстрого чтения фронтом |
| `is_active` | BooleanField | Активно |
| `sorting_order` | IntegerField | Сортировка |

Наследует `CopyMixin` — метод `copy()` с автоматическим подбором уникального кода.

Привязывается к model_line_item через `ElectricControlUnitOption.control_unit_wiring`.

### Кодировки опций

`Allowed*Option` — единый источник истины `encoding` для пары (серия, опция):
- `AllowedControlUnitOption` — кодировка БУ в серии
- `AllowedTurnCounterOption` — кодировка счётчика в серии
- `AllowedSignalProfileOption` — кодировка профиля сигналов в серии

`is_default` остаётся в through-моделях уровня model_line_item.

### Рефакторинг ElectricControlUnitOption (2026-06-18)

**Удалены поля**: `default_signal_profile` (FK), `allowed_signal_profiles` (M2M) — записей не было.

**Добавлено поле**: `control_unit_wiring` (FK → ControlUnitWiring, null=True).

Теперь профиль сигналов и схема подключения живут в `ControlUnitWiring`, а `ElectricControlUnitOption` ссылается на готовую связку. Одна запись `ControlUnitWiring` может быть переиспользована между разными model_line_item.

`encoding` — по-прежнему из `AllowedControlUnitOption` через `resolved_encoding`.

### Архитектура сигналов

Сигналы делятся на **входные** (команды приводу) и **выходные** (обратная связь).

```
SignalRole (direction: input | output)
     │
     ▼
ControlUnitSignalProfileEntry
     ├── signal_role → SignalRole
     ├── sensor → SensorComponent           (выходные роли)
     └── input_signal → InputSignalSpec     (входные роли)
```

| Модель | Приложение | Назначение |
|--------|-----------|-----------|
| `SignalRole` | params | Справочник ролей: OPEN_LIMIT, CLOSE_LIMIT, REMOTE_OPEN, ESD… + поле `direction` (input/output) |
| `InputSignalSpec` | params | Спецификация входного канала БУ: дискретный 24В DC, аналоговый 4-20мА, ESD… |
| `ControlUnitSignalProfile` | params | Типовой профиль сигналов («Стандартные механические SPDT») |
| `ControlUnitSignalProfileEntry` | params | Запись: роль → датчик или входной сигнал (unique: profile+role) |
| `SensorComponent` | pa_controls | Физический датчик: концевик, момéнтник, позиционер (SPDT/DPDT, мех/эл) |

**Входные сигналы** (5 типовых записей): `CU_DI_24V_DC`, `CU_DI_220V_AC`, `CU_DI_ESD_NC`, `CU_AI_4_20MA_PASSIVE`, `CU_AI_4_20MA_ACTIVE`.

## API — админка model_line_item и ControlUnitWiring (добавлен 2026-06-18)

### ModelLineItem

| Метод | URL | Назначение |
|-------|-----|-----------|
| `GET` | `/ea/admin/items/?model_line_id=X` | Список model_line_item для серии |
| `GET` | `/ea/admin/items/<id>/` | Один элемент + все опции (power_supply → CU → wiring) |
| `PUT` | `/ea/admin/items/<id>/` | Сохранить базовые поля + power_supply_options |

GET-ответ включает полную вложенность: `power_supply_options[] → control_unit_options[] → control_unit_wiring → signal_profile, wiring_diagram`.

### ControlUnitWiring — полный CRUD

| Метод | URL | Назначение |
|-------|-----|-----------|
| `GET` | `/ea/admin/wirings/` | Список (только активные) |
| `GET` | `/ea/admin/wirings/<id>/` | Одна запись |
| `POST` | `/ea/admin/wirings/` | Создать |
| `POST` | `/ea/admin/wirings/<id>/` | Копировать (через `CopyMixin.copy()`) |
| `PUT` | `/ea/admin/wirings/<id>/` | Обновить |
| `DELETE` | `/ea/admin/wirings/<id>/` | Удалить (с проверкой использования в ElectricControlUnitOption) |
| `GET` | `/ea/admin/wirings/refs/` | Справочники для формы (БУ, напряжения, профили, SCHEMA-изображения) |

## Фронтенд-админки (добавлены 2026-06-18)

### Модели ЭП — `/admin/ea-models`
- **App**: `frontend/src/apps/ea-model-admin/`
- Левая панель: селект серии → список model_line_item
- Правая панель: редактор базовых полей + карточки напряжений (7 полей)
- Вложенные карточки блоков управления с селектом ControlUnitWiring + превью схемы
- Каскадная фильтрация wiring'ов по типу БУ

### Схемы БУ — `/admin/ea-wirings`
- **App**: `frontend/src/apps/ea-wiring-admin/`
- Таблица CRUD: код, название, БУ, напряжение, профиль, превью
- Модалка создания/редактирования с автозагрузкой справочников
- Кнопка копирования (📋) с гарантией уникальности кода
- Удаление с проверкой использования

## Поток конфигуратора

```
1. Выбор серии (ElectricActuatorModelLine)
2. Выбор модели (ElectricActuatorModelLineItem)
3. Выбор опций:
   a. Напряжение (PowerSupplyOption → params.PowerSupplies)
   b. Блок управления (ControlUnitOption → params.ControlUnitInstalledOption)
      └── encoding из AllowedControlUnitOption (модель БУ одна, коды разные у разных серий)
      └── Счётчики (default_turn_counter + allowed_turn_counters)
      └── Схема подключения (control_unit_wiring → ControlUnitWiring)
   c. Положение безопасности (SafetyPositionOption)
   d. Остальные опции уровня model_line (IP, Exd, …)
4. save() → генерация артикула по шаблону model_line.model_item_code_template
```

## Связанные приложения

| Приложение | Назначение |
|-----------|-----------|
| `params` | Справочники: PowerSupplies, ControlUnitInstalledOption, IP, Exd, TurnCounterOption, SignalRole, InputSignalSpec, ControlUnitSignalProfile |
| `pa_controls` | Датчики: SensorComponent, SignalType, ContactForm, ContactState |
| `core` | CatalogConfig, FilterDefinition, SmartCatalogMixin |
| `media_library` | MediaLibraryItem (изображения схем, категория SCHEMA) |
| `price` | Ценообразование |
| `frontend` | `ea-model-admin`, `ea-wiring-admin`, `ea-constructor` |
