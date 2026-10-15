# pa_controls/views/posi_quickselect.py
"""
GET /api/pa-controls/positioners/quickselect/ — быстрый подбор позиционеров.

Использует BaseQuickSelectView из core/views.py.
"""
from rest_framework.permissions import AllowAny
from core.views import BaseQuickSelectView
from pa_controls.models.positioner_item import PosiModelLineItem
from pa_controls.models.posi_model_line import PosiModelLine
from pa_controls.catalog.posi_config import POSI_CONFIG
from pa_controls.catalog.posi_filter_defs import (
    POSI_FILTER_DEFINITIONS,
    POSI_QUICKSELECT_FILTERS,
)


class PosiQuickSelectView(BaseQuickSelectView):
    permission_classes = [AllowAny]
    quickselect_filters = POSI_QUICKSELECT_FILTERS
    filter_definitions = POSI_FILTER_DEFINITIONS
    model_class = PosiModelLineItem
    model_line_model = PosiModelLine
    select_related = POSI_CONFIG.select_related
    prefetch_fields = None
    auto_select_rules = {}
    catalog_config = POSI_CONFIG
