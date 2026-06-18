"""
Админки приложения electric_actuators.

Каждая админка в отдельном файле, импортируются для регистрации в Django.
"""
from .ea_data_admin import *
from .ea_model_body_admin import *
from .ea_model_line_admin import *
from .ea_cg_holes_set_admin import *
from .ea_actual_actuator_admin import *
from .ea_wiring_diagram_admin import *
from .ea_body_admin import *
from .ea_model_line_item_admin import *
from .ea_model_line_item_options_admin import *
from .ea_actuator_selected_admin import *
from .ea_constructor_admin import *
from .ea_allowed_options_admin import *
from .ea_control_unit_wiring_admin import *

