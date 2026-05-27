# pa_controls/views/catalog.py
"""
API каталога блоков концевых выключателей.

GET  /api/pa-controls/catalog/       — список с фильтрами и поиском
GET  /api/pa-controls/catalog/<id>/  — детальная модель
GET  /api/pa-controls/filters/       — опции фильтров
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from core.views import BaseFilterOptionsView
from pa_controls.models.limit_switch import LimitSwitchBox

SEARCH_FIELDS = ['code', 'name', 'description']
SELECT_RELATED = ['model_line', 'body', 'sensor_variety', 'primary_sensor', 'sku']


class LimitSwitchBoxCatalogView(APIView):
    """
    GET /api/pa-controls/catalog/

    Параметры:
        search              — поиск по code, name, description
        model_line_id       — серия
        sensor_variety_id   — тип сенсора
        points              — количество датчиков (1-4)
        ip_id               — IP
        work_temp_min       — температура от
        work_temp_max       — температура до
        body_material_id    — материал корпуса
        model_line_brand_id — бренд серии
        signal_type_id      — тип сигнала
        exd_id              — взрывозащита
        is_active           — только активные (по умолчанию true)
        limit / offset      — пагинация
    """
    permission_classes = [AllowAny]

    def get(self, request):
        params = request.query_params

        qs = LimitSwitchBox.objects.select_related(*SELECT_RELATED)
        # prefetch не используется — M2M через 'images' с related_name='+' не поддерживается

        is_active = params.get('is_active', 'true')
        if is_active.lower() in ('true', '1'):
            qs = qs.filter(is_active=True)

        filters_applied = {}

        for fd in LimitSwitchBox.FILTER_DEFINITIONS:
            value = params.get(fd.param_name)
            if value is None or value == '' or value == 'all':
                continue

            lookup, converted = fd.build_filter_lookup(value)
            if lookup and converted is not None:
                qs = qs.filter(**{lookup: converted})
                filters_applied[fd.param_name] = value

        # Search
        search = params.get('search', '').strip()
        if search and SEARCH_FIELDS:
            from django.db.models import Q
            q = Q()
            for field in SEARCH_FIELDS:
                q |= Q(**{f'{field}__icontains': search})
            qs = qs.filter(q)
            filters_applied['search'] = search

        total = qs.count()
        limit = int(params.get('limit', 100))
        offset = int(params.get('offset', 0))
        qs = qs[offset:offset + limit]

        data = [item.to_values_dict() for item in qs]

        return Response({
            'data': data,
            'total': total,
            'filters_applied': filters_applied,
            'limit': limit,
            'offset': offset,
        })


class LimitSwitchBoxDetailView(APIView):
    """GET /api/pa-controls/catalog/<id>/"""
    permission_classes = [AllowAny]

    def get(self, request, pk):
        item = get_object_or_404(
            LimitSwitchBox.objects.select_related(*SELECT_RELATED)
            ,
            pk=pk,
        )
        return Response(item.to_dict())


class LimitSwitchBoxFilterOptionsView(BaseFilterOptionsView):
    """
    GET /api/pa-controls/filters/ — опции для FilterSidebar на фронтенде.

    Наследует get() из BaseFilterOptionsView (core/views.py).
    """
    permission_classes = [AllowAny]
    filter_definitions = LimitSwitchBox.FILTER_DEFINITIONS
    model_class = LimitSwitchBox