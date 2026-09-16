# cable_glands/catalog/views_quickselect.py
"""
GET /api/cable-glands/quickselect/ — быстрый подбор (чипсовые фильтры + карточка).
"""
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
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

    def get(self, request):
        """Override: model_line_id is optional — по умолчанию подбор по всем сериям.

        Топ-уровневым фильтром становится «Тип кабеля» (cable_type_id),
        поэтому серия больше не обязательна.
        """
        params = request.query_params
        model_line_id = params.get('model_line_id')
        brand_id = params.get('brand_id')

        qs = self.model_class.objects.filter(is_active=True)

        if model_line_id:
            qs = qs.filter(model_line_id=model_line_id)
        if brand_id:
            qs = qs.filter(model_line__brand_id=brand_id)

        if self.select_related:
            qs = qs.select_related(*self.select_related)
        if self.prefetch_fields:
            qs = qs.prefetch_related(*self.prefetch_fields)

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

        qs = qs.distinct()

        items = [obj.to_dict() for obj in qs[:50]]

        filters_out = {}
        filter_labels = {}
        for fd in (self.filter_definitions or []):
            if fd.param_name not in (self.quickselect_filters or []):
                continue
            options = self._get_filter_options(qs, fd)
            if options:
                filters_out[fd.param_name] = options
                filter_labels[fd.param_name] = fd.label

        ml_info = None
        if model_line_id and self.model_line_model:
            ml_info = self._get_model_line_info(model_line_id)

        defaults = {}
        if self.catalog_config:
            qs_fs = self.catalog_config.filter_sets.get('quickselect')
            if qs_fs:
                defaults = qs_fs.defaults

        return Response({
            'model_line': ml_info,
            'total': qs.count(),
            'items': items,
            'filters': filters_out,
            'filter_labels': filter_labels,
            'defaults': defaults,
        })
