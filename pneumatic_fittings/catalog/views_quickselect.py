# pneumatic_fittings/catalog/views_quickselect.py
"""
GET /api/pneumatic-fittings/quickselect/ — быстрый подбор (чипсовые фильтры + карточка).
"""
from rest_framework.permissions import AllowAny
from core.views import BaseQuickSelectView
from pneumatic_fittings.models import PneumaticFitting, PneumaticFittingModelLine
from pneumatic_fittings.catalog.filter_defs import PNEUMATIC_FITTINGS_FILTER_DEFINITIONS
from pneumatic_fittings.catalog.config import PNEUMATIC_FITTINGS_CONFIG

PNEUMATIC_FITTINGS_QUICKSELECT_FILTERS = [
    'fitting_variety_id', 'body_material_id', 'pipe_material_id',
    'pipe_diameter', 'thread_id', 'thread_inner_outer_id',
]


class PneumaticFittingsQuickSelectView(BaseQuickSelectView):
    permission_classes = [AllowAny]
    quickselect_filters = PNEUMATIC_FITTINGS_QUICKSELECT_FILTERS
    filter_definitions = PNEUMATIC_FITTINGS_FILTER_DEFINITIONS
    model_class = PneumaticFitting
    model_line_model = PneumaticFittingModelLine
    select_related = PNEUMATIC_FITTINGS_CONFIG.select_related
    prefetch_fields = PNEUMATIC_FITTINGS_CONFIG.prefetch_fields
    auto_select_rules = {}
