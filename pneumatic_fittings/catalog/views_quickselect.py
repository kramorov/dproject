# pneumatic_fittings/catalog/views_quickselect.py
"""
GET /api/pneumatic-fittings/quickselect/ — быстрый подбор (чипсовые фильтры + карточка).
Accepts optional model_line_id; when omitted, queries across all series.

Для каталогов глушителей и заглушек queryset ограничен видом каталога
(KindCatalogConfig.get_scoped_queryset).
"""
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from core.views import BaseQuickSelectView
from pneumatic_fittings.models import PneumaticFitting, PneumaticFittingModelLine
from pneumatic_fittings.catalog.filter_defs import PNEUMATIC_FITTINGS_FILTER_DEFINITIONS
from pneumatic_fittings.catalog.config import (
    PNEUMATIC_FITTINGS_CONFIG,
    PNEUMATIC_SILENCERS_CONFIG,
    PNEUMATIC_PLUGS_CONFIG,
    SILENCER_DEFINITIONS,
    PLUG_DEFINITIONS,
)

PNEUMATIC_FITTINGS_QUICKSELECT_FILTERS = [
    'fitting_variety_id', 'body_material_id', 'pipe_material_id',
    'pipe_diameter', 'thread_id', 'thread_inner_outer_id',
]
PNEUMATIC_SILENCER_QUICKSELECT_FILTERS = [
    'thread_id', 'thread_inner_outer_id', 'body_material_id',
]
PNEUMATIC_PLUG_QUICKSELECT_FILTERS = [
    'thread_id', 'thread_inner_outer_id', 'body_material_id',
]


class PneumaticFittingsQuickSelectView(BaseQuickSelectView):
    permission_classes = [AllowAny]
    config = PNEUMATIC_FITTINGS_CONFIG
    quickselect_filters = PNEUMATIC_FITTINGS_QUICKSELECT_FILTERS
    filter_definitions = PNEUMATIC_FITTINGS_FILTER_DEFINITIONS
    model_class = PneumaticFitting
    model_line_model = PneumaticFittingModelLine
    select_related = PNEUMATIC_FITTINGS_CONFIG.select_related
    prefetch_fields = PNEUMATIC_FITTINGS_CONFIG.prefetch_fields
    auto_select_rules = {}

    def get(self, request):
        """Override: model_line_id is optional — no series/brand filter by default."""
        params = request.query_params
        model_line_id = params.get('model_line_id')

        # Базовый queryset — в пределах вида каталога (KindCatalogConfig)
        qs = self.config.get_scoped_queryset()

        if model_line_id:
            qs = qs.filter(model_line_id=model_line_id)

        if self.select_related:
            qs = qs.select_related(*self.select_related)
        if self.prefetch_fields:
            qs = qs.prefetch_related(*self.prefetch_fields)

        # Apply filters from request
        allowed_params = set(self.quickselect_filters or []) | {'work_temp_min', 'work_temp_max'}
        for fd in (self.filter_definitions or []):
            if fd.param_name not in allowed_params:
                continue
            value = params.get(fd.param_name)
            if value is None or value == '' or value == 'all':
                continue
            lookup, converted = fd.build_filter_lookup(value)
            if lookup and converted is not None:
                qs = qs.filter(**{lookup: converted})

        items = [obj.to_dict() for obj in qs[:50]]

        # Filter options with counts
        filters_out = {}
        for fd in (self.filter_definitions or []):
            if fd.param_name not in (self.quickselect_filters or []):
                continue
            options = self._get_filter_options(qs, fd)
            if options:
                filters_out[fd.param_name] = options

        ml_info = None
        if model_line_id and self.model_line_model:
            ml_info = self._get_model_line_info(model_line_id)

        return Response({
            'model_line': ml_info,
            'total': qs.count(),
            'items': items,
            'filters': filters_out,
        })


class PneumaticSilencersQuickSelectView(PneumaticFittingsQuickSelectView):
    """Быстрый подбор глушителей: фильтры резьба/материал корпуса."""

    config = PNEUMATIC_SILENCERS_CONFIG
    quickselect_filters = PNEUMATIC_SILENCER_QUICKSELECT_FILTERS
    filter_definitions = SILENCER_DEFINITIONS
    select_related = PNEUMATIC_SILENCERS_CONFIG.select_related
    prefetch_fields = PNEUMATIC_SILENCERS_CONFIG.prefetch_fields


class PneumaticPlugsQuickSelectView(PneumaticFittingsQuickSelectView):
    """Быстрый подбор заглушек: фильтры резьба/материал корпуса."""

    config = PNEUMATIC_PLUGS_CONFIG
    quickselect_filters = PNEUMATIC_PLUG_QUICKSELECT_FILTERS
    filter_definitions = PLUG_DEFINITIONS
    select_related = PNEUMATIC_PLUGS_CONFIG.select_related
    prefetch_fields = PNEUMATIC_PLUGS_CONFIG.prefetch_fields
