# filter_regulator/views/engineer.py
"""
GET /api/filter-regulator/engineer/ — инженерный каталог с визуальным подбором.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count

from filter_regulator.models import FilterRegulator
from filter_regulator.catalog.filter_defs import FILTER_REGULATOR_FILTER_DEFINITIONS
from filter_regulator.catalog.config import FILTER_REGULATOR_CONFIG


class EngineerCatalogView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        params = request.query_params
        model_line_id = params.get('model_line_id')

        if not model_line_id:
            return Response({'error': 'model_line_id is required'}, status=400)

        qs = FilterRegulator.objects.filter(
            model_line_id=model_line_id, is_active=True
        ).select_related(*FILTER_REGULATOR_CONFIG.select_related)

        for fd in FILTER_REGULATOR_FILTER_DEFINITIONS:
            value = params.get(fd.param_name)
            if value is None or value == '' or value == 'all':
                continue
            lookup, converted = fd.build_filter_lookup(value)
            if lookup and converted is not None:
                qs = qs.filter(**{lookup: converted})

        items = [obj.to_dict() for obj in qs[:50]]

        return Response({
            'model_line': self._get_model_line_info(model_line_id),
            'total': qs.count(),
            'items': items,
        })

    def _get_model_line_info(self, model_line_id):
        from filter_regulator.models import FilterRegulatorModelLine
        try:
            ml = FilterRegulatorModelLine.objects.get(id=model_line_id)
            return {'id': ml.id, 'name': ml.name, 'code': ml.code or ''}
        except FilterRegulatorModelLine.DoesNotExist:
            return None
