# gearbox/views/quickselect.py
"""
GET /api/gearbox/quickselect/ — быстрый подбор (чипсовые фильтры + карточка).

Использует BaseQuickSelectView из core/views.py.
"""
from rest_framework.permissions import AllowAny
from core.views import BaseQuickSelectView
from gearbox.models import GearBox
from gearbox.models.gb_model_line import GearBoxModelLine
from gearbox.services.filters import (
    GEARBOX_FILTER_DEFINITIONS,
    GEARBOX_SELECT_RELATED,
    GEARBOX_PREFETCH_FIELDS,
    GEARBOX_QUICKSELECT_FILTERS,
)


class GearboxQuickSelectView(BaseQuickSelectView):
    permission_classes = [AllowAny]
    quickselect_filters = GEARBOX_QUICKSELECT_FILTERS
    filter_definitions = GEARBOX_FILTER_DEFINITIONS
    model_class = GearBox
    model_line_model = GearBoxModelLine
    select_related = GEARBOX_SELECT_RELATED
    prefetch_fields = GEARBOX_PREFETCH_FIELDS
    auto_select_rules = {}
