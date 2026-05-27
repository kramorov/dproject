# filter_regulator/views/quickselect.py
"""
GET /api/filter-regulator/quickselect/ — быстрый подбор (чипсовые фильтры + карточка).

Использует BaseQuickSelectView из core/views.py.
"""
from rest_framework.permissions import AllowAny
from core.views import BaseQuickSelectView
from filter_regulator.models import FilterRegulator, FilterRegulatorModelLine
from filter_regulator.services.filters import (
    FILTER_REGULATOR_FILTER_DEFINITIONS,
    FILTER_REGULATOR_SELECT_RELATED,
    FILTER_REGULATOR_PREFETCH_FIELDS,
    QUICKSELECT_FILTERS,
)


class FilterRegulatorQuickSelectView(BaseQuickSelectView):
    permission_classes = [AllowAny]
    quickselect_filters = QUICKSELECT_FILTERS
    filter_definitions = FILTER_REGULATOR_FILTER_DEFINITIONS
    model_class = FilterRegulator
    model_line_model = FilterRegulatorModelLine
    select_related = FILTER_REGULATOR_SELECT_RELATED
    prefetch_fields = FILTER_REGULATOR_PREFETCH_FIELDS
    auto_select_rules = {
        'filtration_rating_min': 'max',
        'flow_rate_min': 'min',
    }
