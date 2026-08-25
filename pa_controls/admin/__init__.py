# pa_controls/admin/__init__.py
from .limit_switch_admin import (
    LimitSwitchSensorVarietyAdmin,
    LimitSwitchModelLineAdmin, LimitSwitchBodyAdmin, LimitSwitchBoxAdmin

)
from .pa_control_mounting_admin import PaControlMountingStandardAdmin
from .positioner_admin import (
    ActingTypeAdmin,
    LeverOptionAdmin,
    SmartCapabilityOptionAdmin,
    SmartCapabilitySetAdmin,
    PosiModelLineAdmin,
    PosiModelLineItemAdmin,
)

__all__ = [
    'LimitSwitchSensorVarietyAdmin',
    'LimitSwitchModelLineAdmin',
    'PaControlMountingStandardAdmin',
    'LimitSwitchBodyAdmin',
    'LimitSwitchBoxAdmin',
    'ActingTypeAdmin',
    'LeverOptionAdmin',
    'SmartCapabilityOptionAdmin',
    'SmartCapabilitySetAdmin',
    'PosiModelLineAdmin',
    'PosiModelLineItemAdmin',
]

