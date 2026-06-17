# electric_actuators — Электроприводы

Приложение Django для каталога и конфигуратора электроприводов.

## Архитектура

```
electric_actuators/
├── models/
│   ├── ea_model_line.py          # ElectricActuatorModelLine — серия (ABRA-BUV-VF826)
│   ├── ea_model_line_item.py     # ElectricActuatorModelLineItem — модель в серии (DN100)
│   ├── ea_model_body.py          # ModelBody — корпус привода
│   ├── ea_body.py                # ElectricActuatorBody — таблица корпусов
│   ├── ea_cg_holes_set.py        # CableGlandHolesSet — наборы кабельных вводов
│   ├── ea_options.py             # Through-модели опций уровня model_line
│   ├── ea_model_line_item_options.py  # Through-модели опций уровня model_line_item
│   ├── ea_allowed_options.py     # Allowed*Option — кодировки опций для серии
│   ├── ea_actuator_constructor.py # Конструктор (пошаговый подбор)
│   ├── ea_actuator_selected.py   # Выбранная конфигурация (сохранённый подбор)
│   ├── ea_data.py                # ElectricActuatorData — технические данные
│   └── ea_wiring_diagram.py      # WiringDiagram — схема подключения
├── admin/                        # Админки (по файлу на модель)
├── api/                          # REST API
├── services/                     # Бизнес-логика
├── graphql/                      # GraphQL схема
├── static/                       # Статика
└── templates/                    # Шаблоны
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
- `ElectricControlUnitOption` — блок управления + счётчики + сигналы

### Кодировки опций

`Allowed*Option` — единый источник истины `encoding` для пары (серия, опция):
- `AllowedControlUnitOption` — кодировка БУ в серии
- `AllowedTurnCounterOption` — кодировка счётчика в серии
- `AllowedSignalProfileOption` — кодировка профиля сигналов в серии

`is_default` остаётся в through-моделях уровня model_line_item.

### Конструктор и Selected

| Модель | Назначение |
|--------|-----------|
| `ElectricActuatorConstructor` | Пошаговый подбор: модель → напряжение → БУ → опции. FK на реальные опции |
| `ElectricActuatorSelected` | Сохранённая конфигурация с артикулом и валидацией |

## Поток конфигуратора

```
1. Выбор серии (ElectricActuatorModelLine)
2. Выбор модели (ElectricActuatorModelLineItem)
3. Выбор опций:
   a. Напряжение (PowerSupplyOption → params.PowerSupplies)
   b. Блок управления (ControlUnitOption → params.ControlUnitInstalledOption)
      └── encoding из AllowedControlUnitOption (модель БУ одна, коды разные у разных серий)
      └── Счётчики (default_turn_counter + allowed_turn_counters)
      └── Сигналы (default_signal_profile + allowed_signal_profiles)
   c. Положение безопасности (SafetyPositionOption)
   d. Остальные опции уровня model_line (IP, Exd, …)
4. save() → генерация артикула по шаблону model_line.model_item_code_template
```

## Связанные приложения

| Приложение | Назначение |
|-----------|-----------|
| `params` | Справочники: PowerSupplies, ControlUnitInstalledOption, IP, Exd, TurnCounterOption, SignalRole, ControlUnitSignalProfile |
| `pa_controls` | Датчики: SensorComponent, SignalType, ContactForm, ContactState |
| `core` | CatalogConfig, FilterDefinition, SmartCatalogMixin |
| `price` | Ценообразование |
