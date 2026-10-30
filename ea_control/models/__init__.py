# ea_control/models/__init__.py
"""
Модели приложения ea_control (блоки управления электроприводов).

Структура:

- ``abstract.py`` — абстракции паттерна «узлы/слоты/матрицы/правила»
  (после отладки переезжают в core);
- ``dictionaries.py`` — копии справочников ЭП (сигналы/формы/протоколы/
  устройства/обогрев/размещение) + новый справочник CuCapability;
- ``cu_power.py`` — справочники схемотехники цепей управления (из черновика);
- ``control_unit.py`` — физическая сущность «тип БУ» (ControlUnit);
- ``cu_config.py`` — паттерн-модели конфигурации БУ (узел/слот/опция/
  матрица/правило).

Черновик с набросками справочников БУ сохранён в ``_draft_legacy_models.py``
(не импортируется Django).
"""
from ea_control.models.abstract import (  # noqa: F401
    AbstractConfigNode,
    AbstractConfigSlot,
    AbstractSlotOption,
    AbstractSlotMatrixEntry,
    AbstractSlotRule,
    AbstractConfigSnapshot,
    ConfigSelectionMode,
    ConfigSlotKind,
    ConfigAvailability,
    ConfigRuleAction,
    ConfigRuleOperator,
)
from ea_control.models.dictionaries import (  # noqa: F401
    CuControlSignalForm,
    CuFeedbackSignalForm,
    CuControlSignal,
    CuFeedbackSignal,
    CuCommProtocol,
    CuFeedbackDevice,
    CuHeaterSupply,
    CuLocationOption,
    CuCapability,
    CuLocalControlType,
    CuDisplayType,
    CuUnitPowerSource,
)
from ea_control.models.cu_power import (  # noqa: F401
    CuSignalPowerSource,
    CuSignalPower,
    CuPolarity,
    CuControlLogic,
)
from ea_control.models.control_unit import (  # noqa: F401
    ControlUnitKind,
    ControlUnit,
)
from ea_control.models.cu_config import (  # noqa: F401
    CuSectionNode,
    CuSlot,
    CuOptionKind,
    CuSlotOption,
    CuMatrixMode,
    CuMatrixEntry,
    CuSlotRule,
)
