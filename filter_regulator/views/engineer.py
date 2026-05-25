# filter_regulator/views/engineer.py
"""
GET /api/filter-regulator/engineer/ — инженерный каталог с визуальным подбором.

Параметры:
    model_line_id    — обязательный, главный фильтр (серия)
    filtration_rating_min — тонкость фильтрации, мкм
    body_material_id — материал корпуса
    flow_rate_min    — расход не менее, л/мин
    gauge_port_size_id — резьба манометра
    work_temp_min    — температура от
    work_temp_max    — температура до

Возвращает:
    {
        "model_line": {id, name},
        "items": [...] — подходящие модели,
        "filters": {
            "filtration_rating_min": [{value, label, count}, ...],
            "body_material_id": [{id, name, count}, ...],
            ...
        }
    }
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count

from filter_regulator.models import FilterRegulator
from filter_regulator.services.filters import (
    FILTER_REGULATOR_FILTER_DEFINITIONS,
    FILTER_REGULATOR_SELECT_RELATED,
    FILTER_REGULATOR_PREFETCH_FIELDS,
    ENGINEER_FILTERS,
)


class EngineerCatalogView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        params = request.query_params
        model_line_id = params.get('model_line_id')

        if not model_line_id:
            return Response({'error': 'model_line_id is required'}, status=400)

        qs = FilterRegulator.objects.filter(
            model_line_id=model_line_id, is_active=True
        ).select_related(*FILTER_REGULATOR_SELECT_RELATED)

        # Применяем подфильтры
        for fd in FILTER_REGULATOR_FILTER_DEFINITIONS:
            if fd.param_name not in ENGINEER_FILTERS and fd.param_name not in ('work_temp_min', 'work_temp_max'):
                continue
            value = params.get(fd.param_name)
            if value is None or value == '' or value == 'all':
                continue
            lookup, converted = fd.build_filter_lookup(value)
            if lookup and converted is not None:
                qs = qs.filter(**{lookup: converted})

        # Подходящие модели
        items = [obj.to_dict() for obj in qs[:50]]

        # Строим опции для каждого ENGINEER-фильтра
        filters_out = {}
        for fd in FILTER_REGULATOR_FILTER_DEFINITIONS:
            if fd.param_name not in ENGINEER_FILTERS:
                continue
            options = self._get_filter_options(qs, fd)
            if options:
                filters_out[fd.param_name] = options

        return Response({
            'model_line': self._get_model_line_info(model_line_id),
            'total': qs.count(),
            'items': items,
            'filters': filters_out,
        })

    def _get_filter_options(self, qs, fd):
        """Собрать доступные значения фильтра с подсчётом."""
        from core.models.smart_catalog_mixin import FilterType as _FT
        field_name = fd.model_field

        if fd.filter_type in (_FT.EXACT,):
            # FK — группируем по ID, получаем названия
            try:
                # Находим связанную модель
                parts = field_name.split('__')
                from filter_regulator.models import FilterRegulator as FR
                rel_model = FR
                for part in parts:
                    fld = rel_model._meta.get_field(part)
                    if fld.is_relation:
                        rel_model = fld.remote_field.model

                rows = (
                    qs.values(f'{field_name}_id')
                    .annotate(count=Count('id'))
                    .order_by(f'{field_name}_id')
                )
                ids = [r[f'{field_name}_id'] for r in rows if r[f'{field_name}_id'] is not None]
                if not ids:
                    return []

                objects = rel_model.objects.filter(id__in=ids)
                obj_map = {obj.id: obj for obj in objects}

                result = []
                for row in rows:
                    oid = row[f'{field_name}_id']
                    if oid and oid in obj_map:
                        result.append({
                            'id': oid,
                            'name': str(obj_map[oid]),
                            'count': row['count'],
                        })
                return result
            except Exception:
                return []

        elif fd.filter_type in (_FT.MIN,):
            # Числовое поле — уникальные значения
            values = (
                qs.values_list(field_name, flat=True)
                .distinct()
                .order_by(field_name)
            )
            return [
                {'value': v, 'label': str(v), 'count': qs.filter(**{f'{field_name}__gte': v}).count()}
                for v in values if v is not None
            ]

        return []

    def _get_model_line_info(self, model_line_id):
        from filter_regulator.models import FilterRegulatorModelLine
        try:
            ml = FilterRegulatorModelLine.objects.get(id=model_line_id)
            return {'id': ml.id, 'name': ml.name, 'code': ml.code or ''}
        except FilterRegulatorModelLine.DoesNotExist:
            return None
