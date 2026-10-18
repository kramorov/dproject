# Анализ моделей electric_actuators — Chief System Architect / Chief Design Engineer

Дата: 2026-10-18. Цель: подготовка фазы 7 (удаление старого) и приведение ЭП к
эталонной схеме каталога, как у пневмоприводов.

## 1. Эталон (пневмоприводы, согласовано ранее)

- **Карточка каталога** `PneumaticActuatorCatalogItem` — эталонная модель:
  `SKUMixin` (sync_sku → SKU с GenericFK), `TemplateMixin` (name/description
  из шаблонов серии), артикул из `model_item_code_template` через encoding
  через-опций. Каталог = набор таких карточек со стандартными опциями.
- **Конфигуратор** собирает нестандартную конфигурацию → создаётся карточка
  (не эталонная) + SKU; в каталоге не отображается.
- Старые `PneumaticActuatorSelected`/`PneumaticActuatorConstructor` оставлены
  временно (отладка), с мостиком `source_model_line_item` (этап P8).

## 2. Вердикты по моделям electric_actuators

### 2.1 Ядро новой схемы — ОСТАВИТЬ (активно развивается)

- `ElectricActuatorModelLine` — серия (носитель шаблонов; фаза 6 добавит
  name_template/description_template/model_item_code_template с плейсхолдерами сигналов).
- `ElectricActuatorBodyTable` / `ElectricActuatorBody` / `ElectricActuatorModelLineItem` —
  корпус и модель (карточка-источник стандартных опций).
- `CableGlandHolesSet` (+kind CONNECTOR_PLUG) / `CableGlandHolesSetBodyOption`.
- Через-опции серии (НЕ сигнальные, остаются): `ElectricTemperatureOption`
  (уже +code+heater_supply), `ElectricIpOption`, `ElectricExdOption`,
  `ElectricBodyCoatingOption`, `ElectricBodyColorOption`, `ElectricHandWheelOption`,
  `ElectricTurnAngleOption`.
- `AllowedControlUnitOption` — новая связка «серия×БУ×напряжение» (+encoding/
  ext_encoding/cu_power_supply).
- Вся новая сигнальная схема: `EaSignalForm/EaControlSignal/EaFeedbackSignal/
  EaCommProtocol/EaFeedbackDevice/EaSignalSlot/EaSlotOption/EaSignalMatrixEntry/
  EaWiringDiagramBinding`.

### 2.2 НУЖНА новая модель (ответ на вопрос Selected vs Constructor)

Ни `ElectricActuatorSelected`, ни `ElectricActuatorConstructor` не являются
эталонной карточкой:

- `ElectricActuatorSelected` (code/ext_code/description + selected_* ссылки +
  `is_unique`) — финальная конфигурация, но БЕЗ SKUMixin и TemplateMixin;
  фактически legacy-карточка.
- `ElectricActuatorConstructor` (71 КБ, _OPTION_CONFIG, мягкая валидация) —
  РАБОЧИЙ ЧЕРНОВИК конфигуратора (состояние UI), не должен быть источником SKU.

**Решение: вводим `ElectricActuatorCatalogItem`** — эталонная каталожная
карточка исполнения ЭП, по контракту `PneumaticActuatorCatalogItem`:
SKUMixin + TemplateMixin (+ ImageGallery/TechDoc/EquipmentType при
необходимости); поля: model_line_item FK, БУ/напряжение/режим, через-опции
(IP/Exd/температура/покрытие/цвет/угол/штурвал/ввод кабелей/положение
безопасности), **M2M на EaSignalMatrixEntry** (выбранные строки матрицы),
`is_catalog` (эталон каталога) / `is_unique` (нестандартная); артикул —
`model_item_code_template` + ext-код из выбранных строк (`selection_ext_code`).

- `ElectricActuatorConstructor` — остаётся черновиком UI (как у пневмо);
  хранит те же поля через-опций + выбор матричных строк; создаёт/обновляет
  карточку. После стабилизации можно свести к временному состоянию.
- `ElectricActuatorSelected` — заменить карточкой; данные переносятся
  data-миграцией (переезд, как договаривались), затем удалить.

### 2.3 УДАЛИТЬ в фазе 7 (сигнальные legacy, заменены матрицей)

- `ElectricEndSwitchesOption`, `ElectricWaySwitchesOption`,
  `ElectricTorqueSwitchesOption` → слоты LIMIT/WAY/TORQUE.
- `ElectricBlinkerOption`, `ElectricMechanicalIndicatorOption` → слот INDICATOR.
- `ElectricOperatingModeOption` → ось mode матрицы.
- `ElectricControlUnitInstalledOption` (через-опция БУ серии) →
  `AllowedControlUnitOption` + матрица.
- `ElectricControlUnitOption` (БУ×напряжение на модели) → матрица;
  encoding — в `AllowedControlUnitOption` (уже перенесён, миграция 0058).
- `AllowedSignalProfileOption` — мёртв (проверено: только админка).
- `ControlUnitWiring` + поле `ElectricControlUnitOption.control_unit_wiring` →
  `EaWiringDiagramBinding`.
- `params.ControlUnitSignalProfile` + Entry — после переноса (затрагивает
  params; отдельным шагом).
- Закомментированные файлы-пустышки: `ea_actual_actuator.py`,
  `ea_wiring_diagram.py` — удалить файлы.

### 2.4 УДАЛИТЬ позже (перенести данные)

- `AllowedTurnCounterOption` — encoding счётчиков → слот TURN_COUNTER
  (после решения о кодах MECH-вариантов).
- `ElectricPowerSupplyOption` (моторные данные: токи/время/момент) — данные
  переносятся в `ElectricActuatorCatalogItem` (напряжение + моторные поля);
  **зависимость: `price.EAPriceConstructor` FK → ElectricPowerSupplyOption** —
  переносить вместе.
- `ElectricSafetyPositionOption` (привязана к PS-опции) — не сигнальная;
  перенести в карточку вместе с PS.
- `ElectricActuatorData` + `ModelLine` + `ModelBody` — древний каталог;
  единственный runtime-потребитель — `data_processor/processor.py`
  (старый импорт прайсов) — удалить после перевода импорта на новые модели.

## 3. План фазы 7 (порядок)

1. Создать `ElectricActuatorCatalogItem` (SKUMixin + TemplateMixin +
   M2M matrix rows) + миграция + перенос данных из `ElectricActuatorSelected`
   и моторных данных из `ElectricPowerSupplyOption` (data-миграция, выгрузка
   уже есть: ea_signals_export_2026-10-18.json).
2. Удалить мёртвые (2.3): AllowedSignalProfileOption, закомментированные
   файлы; через-опции переключателей/блинкера/индикатора/режима/БУ; 
   ControlUnitWiring; ElectricControlUnitOption (+ поле в PS-опции).
3. Конструктор: убрать сигнальные поля (_OPTION_CONFIG), оставить
   не-сигнальные + выбор матричных строк; экраны API.
4. Починить `ensure_all_default_options_exist` (пре-экзист баг передачи серии
   в ElectricWaySwitchesOption) — с удалением опций уйдёт сам.
5. Проверка: тесты, `makemigrations --check`, фронт-смоук каталога ЭП.
6. Позже (2.4): TurnCounter encoding, price/data_processor переносы.

## 4. Вопросы на подтверждение

1. Имя карточки: `ElectricActuatorCatalogItem` (симметрия с пневмо) — ок?
2. `ElectricActuatorConstructor` оставляем как черновик конфигуратора
   (без SKU), как у пневмо — ок?
3. Удаление из п.2.3 делаем в этом заходе (после подтверждения)?
4. `price.EAPriceConstructor` трогать сейчас или оставить FK на
   ElectricPowerSupplyOption до этапа 2.4?
