# gearbox/views/quickselect.py
"""
GET /api/gearbox/quickselect/ — быстрый подбор (чипсовые фильтры + карточка).
"""
from rest_framework.permissions import AllowAny
from core.views import BaseQuickSelectView
from gearbox.models import GearBox
from gearbox.models.gb_model_line import GearBoxModelLine
from gearbox.catalog.filter_defs import GEARBOX_FILTER_DEFINITIONS
from gearbox.catalog.config import GEARBOX_CONFIG

GEARBOX_QUICKSELECT_FILTERS = [
    'body_material_id', 'min_work_torque', 'mounting_plate_top_id',
]


class GearboxQuickSelectView(BaseQuickSelectView):
    permission_classes = [AllowAny]
    quickselect_filters = GEARBOX_QUICKSELECT_FILTERS
    filter_definitions = GEARBOX_FILTER_DEFINITIONS
    model_class = GearBox
    model_line_model = GearBoxModelLine
    select_related = GEARBOX_CONFIG.select_related
    prefetch_fields = GEARBOX_CONFIG.prefetch_fields
    auto_select_rules = {}
    catalog_config = GEARBOX_CONFIG
