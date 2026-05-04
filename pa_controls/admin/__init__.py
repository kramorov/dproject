# pa_controls/admin/__init__.py
from .limit_switch_admin import (
    LimitSwitchSensorVarietyAdmin ,
    LimitSwitchModelLineAdmin , LimitSwitchBodyAdmin

)
from .pa_control_mounting_admin import PaControlMountingStandardAdmin

__all__ = [
    'LimitSwitchSensorVarietyAdmin',
    'LimitSwitchModelLineAdmin',
    'PaControlMountingStandardAdmin',
    'LimitSwitchBodyAdmin'

]

