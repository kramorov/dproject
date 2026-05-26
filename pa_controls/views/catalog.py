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


class LimitSwitchBoxFilterOptionsView(APIView):
    """GET /api/pa-controls/filters/?scope=used"""
    permission_classes = [AllowAny]

    def get(self, request):
        scope = request.query_params.get('scope', 'used')
        all_options = LimitSwitchBox.get_filter_options()

        if scope == 'used':
            active_qs = LimitSwitchBox.objects.filter(is_active=True)
            # Filter each option to only include values that exist in active records
            for key, opt_list in all_options.items():
                if not opt_list or not isinstance(opt_list, list) or len(opt_list) == 0:
                    continue
                item = opt_list[0]
                if not isinstance(item, dict) or 'id' not in item:
                    continue
                # Map param_name to actual model field for values_list
                field_map = {
                    'model_line_brand_id': 'model_line__brand_id',
                    'ip_id': 'ip_id',
                    'exd_id': 'exd_id',
                    'sensor_variety_id': 'sensor_variety_id',
                    'signal_type_id': 'primary_sensor__signal_type_id',
                    'body_material_id': 'body_material_id',
                }
                db_field = field_map.get(key, key.replace('_id', '_id'))
                # Remove _id suffix and try direct field
                if db_field == key:
                    # Try without _id first
                    clean = key.replace('_id', '')
                    try:
                        used_ids = set(active_qs.values_list(clean, flat=True).distinct())
                    except Exception:
                        try:
                            used_ids = set(active_qs.values_list(db_field, flat=True).distinct())
                        except Exception:
                            continue
                else:
                    try:
                        used_ids = set(active_qs.values_list(db_field, flat=True).distinct())
                    except Exception:
                        continue
                all_options[key] = [o for o in opt_list if o['id'] in used_ids]

        return Response(all_options)
