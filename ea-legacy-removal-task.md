# Задача: удаление legacy-связки ElectricActuatorData / ModelBody / ModelLine (ЭП)

> Статус: запланировано 2026-10-18, не начато. Основание: ревью/анализ моделей
> ЭП (ea-models-analysis.md) — «не оставлять старые механизмы».

## Что удалить

- `electric_actuators.ModelLine` — старая модель серии ЭП (6 строк в БД),
  дублирует `ElectricActuatorModelLine`; FK-поля опций (`default_ip` →
  `params.IpOption`, `default_hand_wheel`, `allowed_*` и т.п.) заменены
  through-моделями новой схемы.
- `electric_actuators.ModelBody` — старый корпус (FK → ModelLine).
- `electric_actuators.ElectricActuatorData` — старая таблица данных приводов
  (FK → ModelLine), заменена ElectricActuatorBody/ModelLineItem.

## Порядок (как фаза 7)

1. **Анализ связей**: полный список FK/M2M на эти модели по всем приложениям
   (`_meta.related_objects`, grep по кодовой базе) — могут быть неожиданные
   ссылки (пример: price.EAPriceConstructor, data_processor).
2. **Перенос/архивация данных**: проверить, всё ли из `ElectricActuatorData`/
   `ModelBody` перенесено в новую схему (ElectricActuatorBody,
   ElectricActuatorBodyTable, ElectricActuatorModelLineItem); выгрузить остаток
   в JSON-архив (паттерн ea_signals_export_2026-10-18.json).
3. **Чистка кода**: админки (ea_data_admin, ea_model_body_admin), вью, сериализаторы,
   команды, ссылки в других приложениях.
4. **Миграция DeleteModel** ×3 (одной миграцией, reversable-проверка round-trip).
5. Тесты + `makemigrations --check`.

## Связанные открытые хвосты

- `price.EAPriceConstructor` (FK на `ElectricPowerSupplyOption`) — отдельная
  задача, согласована.
- `AllowedTurnCounterOption.encoding` → слот TURN_COUNTER (перенос кодировок).
- `ElectricPowerSupplyOption`/`ElectricSafetyPositionOption` → карточка
  (моторные данные, положение безопасности).
