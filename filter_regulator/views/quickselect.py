# filter_regulator/views/quickselect.py
"""
GET /api/filter-regulator/quickselect/ — быстрый подбор (чипсовые фильтры + карточка).
"""
from rest_framework.permissions import AllowAny
from core.views import BaseQuickSelectView
from filter_regulator.models import FilterRegulator, FilterRegulatorModelLine
from filter_regulator.catalog.filter_defs import FILTER_REGULATOR_FILTER_DEFINITIONS
from filter_regulator.catalog.config import FILTER_REGULATOR_CONFIG

QUICKSELECT_FILTERS = [
    'filtration_rating_min', 'body_material_id', 'flow_rate_min', 'thread_id',
]


class FilterRegulatorQuickSelectView(BaseQuickSelectView):
    permission_classes = [AllowAny]
    quickselect_filters = QUICKSELECT_FILTERS
    filter_definitions = FILTER_REGULATOR_FILTER_DEFINITIONS
    model_class = FilterRegulator
    model_line_model = FilterRegulatorModelLine
    select_related = FILTER_REGULATOR_CONFIG.select_related
    prefetch_fields = FILTER_REGULATOR_CONFIG.prefetch_fields
    auto_select_rules = {
        'filtration_rating_min': 'max',
        'flow_rate_min': 'min',
    }
    catalog_config = FILTER_REGULATOR_CONFIG
