# solenoid_valves/catalog/views_quickselect.py
"""
GET /api/solenoid-valves/quickselect/ — быстрый подбор (чипсовые фильтры + карточка).
"""
from rest_framework.permissions import AllowAny
from core.views import BaseQuickSelectView
from solenoid_valves.models import DirectionValve
from solenoid_valves.models.dv_model_line import DirectionalValveModelLine
from solenoid_valves.catalog.filter_defs import SOLENOID_VALVES_FILTER_DEFINITIONS
from solenoid_valves.catalog.config import SOLENOID_VALVES_CONFIG

SOLENOID_VALVES_QUICKSELECT_FILTERS = [
    'function_id', 'actuation_id', 'power_supply_id',
    'body_material_id', 'pneumatic_connection_id',
    'pneumatic_connection_thread_id', 'work_temp_min', 'ip_id', 'exd_id',
]


class SolenoidValvesQuickSelectView(BaseQuickSelectView):
    permission_classes = [AllowAny]
    quickselect_filters = SOLENOID_VALVES_QUICKSELECT_FILTERS
    filter_definitions = SOLENOID_VALVES_FILTER_DEFINITIONS
    model_class = DirectionValve
    model_line_model = DirectionalValveModelLine
    select_related = SOLENOID_VALVES_CONFIG.select_related
    prefetch_fields = SOLENOID_VALVES_CONFIG.prefetch_fields
    auto_select_rules = {}
    catalog_config = SOLENOID_VALVES_CONFIG