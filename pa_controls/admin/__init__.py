# pa_controls/admin/__init__.py
from .limit_switch_admin import (
    LimitSwitchSensorVarietyAdmin,
    LimitSwitchOutputAdmin,
    LimitSwitchModelLineAdmin

)
from .pa_control_mounting_admin import PaControlMountingStandardAdmin

__all__ = [
    'LimitSwitchSensorVarietyAdmin',
    'LimitSwitchOutputAdmin',
    'LimitSwitchModelLineAdmin',
    'PaControlMountingStandardAdmin',

]

