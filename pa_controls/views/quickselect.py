# pa_controls/views/quickselect.py
"""
GET /api/pa-controls/quickselect/ — быстрый подбор (чипсовые фильтры + карточка).

Использует BaseQuickSelectView из core/views.py.
"""
from rest_framework.permissions import AllowAny
from core.views import BaseQuickSelectView
from pa_controls.models.limit_switch import LimitSwitchBox
from pa_controls.models.lsb_model_line import LimitSwitchModelLine
from pa_controls.catalog.config import LIMIT_SWITCH_CONFIG


class LimitSwitchBoxQuickSelectView(BaseQuickSelectView):
    permission_classes = [AllowAny]
    quickselect_filters = LimitSwitchBox.QUICKSELECT_FILTERS
    filter_definitions = LimitSwitchBox.FILTER_DEFINITIONS
    model_class = LimitSwitchBox
    model_line_model = LimitSwitchModelLine
    select_related = LimitSwitchBox.SELECT_RELATED_FIELDS
    prefetch_fields = None
    auto_select_rules = {}
    catalog_config = LIMIT_SWITCH_CONFIG
