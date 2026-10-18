# Анализ моделей electric_actuators — Chief System Architect / Chief Design Engineer

Дата: 2026-10-18 (актуализировано вечером — после фаз 7 и 9). Цель: приведение ЭП
к эталонной схеме каталога, как у пневмоприводов.

## 1. Эталон (пневмоприводы)

- **Карточка каталога** `PneumaticActuatorCatalogItem` — эталонная модель:
  `SKUMixin` (sync_sku → SKU с GenericFK), `TemplateMixin` (name/description
  из шаблонов серии → EquipmentType), артикул из `model_item_code_template`
  через encoding через-опций. Каталог = набор таких карточек.
- **Конфигуратор** собирает нестандартную конфигурацию → создаётся карточка
  (не эталонная) + SKU.

## 2. Состояние моделей electric_actuators

### 2.1 Ядро новой схемы — реализовано и работает

- `ElectricActuatorModelLine` — серия: `model_item_code_template`,
  `ext_encoding_template` (шаблонов name/description у серии нет — по цепочке
  TemplateMixin берутся из EquipmentType 'electric-actuator').
- `ElectricActuatorBodyTable` / `ElectricActuatorBody` / `ElectricActuatorModelLineItem`.
- Через-опции серии (не сигнальные): `ElectricTemperatureOption` (+code+heater_supply,
  `_localized_base_name`), `ElectricIpOption`, `ElectricExdOption`
  (`_localized_base_name` — без серии), `ElectricBodyCoatingOption`,
  `ElectricBodyColorOption`, `ElectricHandWheelOption`, `ElectricTurnAngleOption`.
- `AllowedControlUnitOption` — связка «серия×БУ×напряжение» (+encoding/
  ext_encoding/cu_power_supply); резолвер `resolve_cu_pair` (модельные запреты).
- Сигнальная схема (фаза 9): `EaSignalForm/EaControlSignal/EaFeedbackSignal/
  EaCommProtocol/EaFeedbackDevice/EaSignalSlot/EaSlotOption/EaSignalMatrixEntry/
  EaWiringDiagramBinding`; матрица = **профиль БУ** (строки без скоупов),
  резолвер `services/ea_signal_resolver.py`, ext-код `services/ea_ext_code.py`.
- `EaAccessDeviceOption` + `ControlUnitAccessDeviceOption` (для БУ кроме
  int-o/int-l/int-n — только «нет»).

### 2.2 Карточка каталога — создана (фаза 7–8)

- **`ElectricActuatorCatalogItem`** — эталонная каталожная карточка исполнения
  ЭП по контракту `PneumaticActuatorCatalogItem`: SKUMixin + TemplateMixin
  (реестр `ea_catalog_item_fields.py`, плейсхолдеры cu_/ctl_/fb_/прочие,
  локализация через localized_name), M2M `matrix_rows` (EaSignalMatrixEntry),
  is_catalog/is_unique, артикул = `model_item_code_template` + ext
  (`selection_ext_code`), контекст БУ/напряжение/режим.
- `ElectricActuatorConstructor` — черновик конфигуратора: выбор модели/опций +
  `selected_matrix_rows` (профиль БУ); генерирует описание из шаблонов
  EquipmentType (TemplateMixin, skip_auto_generate для name-артикула);
  превью — локализовано (Accept-Language). Создание карточек из конструктора —
  следующий шаг (список опций определяет пользователь после проверки).
- `ElectricActuatorSelected` — legacy-карточка, заменяется
  `ElectricActuatorCatalogItem` (перенос данных — data-миграцией).

### 2.3 УДАЛЕНО в фазе 7 (сигнальные legacy)

`ElectricEndSwitchesOption`, `ElectricWaySwitchesOption`,
`ElectricTorqueSwitchesOption`, `ElectricBlinkerOption`,
`ElectricMechanicalIndicatorOption`, `ElectricOperatingModeOption`,
`ElectricControlUnitInstalledOption`, `ElectricControlUnitOption`,
`AllowedSignalProfileOption`, `ControlUnitWiring` (+ файлы
`ea_control_unit_wiring.py`, `ea_actual_actuator.py`, `ea_wiring_diagram.py` и
команды compare/export/transfer_ea_*). Миграция 0060. Конструктор/админки/API
очищены (ревью №8 дорезало рантайм-ссылки).

### 2.4 УДАЛИТЬ позже (перенести данные) — актуальные хвосты

- `ElectricPowerSupplyOption` (моторные данные: токи/время/момент) — перенос в
  карточку; **зависимость: `price.EAPriceConstructor` FK → ElectricPowerSupplyOption** —
  переносить вместе.
- `ElectricSafetyPositionOption` (привязана к PS-опции) — перенести вместе с PS.
- `ElectricActuatorData` + `ModelLine` + `ModelBody` — древний каталог;
  потребитель — `data_processor/processor.py` — подробный план в
  `ea-legacy-removal-task.md`.
- `AllowedTurnCounterOption` — encoding счётчиков → слот TURN_COUNTER.

## 3. Что осталось (порядок)

1. Проверка конструктора пользователем (`/admin/ea-constructor`, локали /en/ /cn/).
2. Генерация карточек `ElectricActuatorCatalogItem` из конструктора (список
   опций — по результатам проверки).
3. Хвосты 2.4 (price/data_processor, legacy-модели) — по `ea-legacy-removal-task.md`.
4. Отдельно: генератор wiring-диаграмм (фаза 8), каталог S2/стартера.
