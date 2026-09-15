# cable_glands/catalog/views_quickselect.py
"""
GET /api/cable-glands/quickselect/ — быстрый подбор (чипсовые фильтры + карточка).
"""
from rest_framework.permissions import AllowAny
from core.views import BaseQuickSelectView
from cable_glands.models import CableGland
from cable_glands.models.cg_model_line import CableGlandModelLine
from cable_glands.catalog.filter_defs import CABLE_GLAND_FILTER_DEFINITIONS
from cable_glands.catalog.config import CABLE_GLAND_CONFIG

CABLE_GLAND_QUICKSELECT_FILTERS = [
    'thread_id', 'body_material_id', 'exd_id', 'ip_id',
    'cable_type_id',
    'cable_diameter_min', 'cable_diameter_max',
    'work_temp_min',
]


class CableGlandQuickSelectView(BaseQuickSelectView):
    permission_classes = [AllowAny]
    quickselect_filters = CABLE_GLAND_QUICKSELECT_FILTERS
    filter_definitions = CABLE_GLAND_FILTER_DEFINITIONS
    model_class = CableGland
    model_line_model = CableGlandModelLine
    select_related = CABLE_GLAND_CONFIG.select_related
    prefetch_fields = CABLE_GLAND_CONFIG.prefetch_fields
    auto_select_rules = {}
    catalog_config = CABLE_GLAND_CONFIG
