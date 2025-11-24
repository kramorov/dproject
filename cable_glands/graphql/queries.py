import graphene
from django.db.models import Q
from .types import CableGlandModelLineNode, CableGlandItemNode
from ..models import CableGlandModelLine, CableGlandItem


class Query(graphene.ObjectType):
    cg_cable_gland_model_lines = graphene.List(
        CableGlandModelLineNode,
        filters=graphene.Argument(graphene.JSONString)
    )

    cg_cable_gland_items = graphene.List(
        CableGlandItemNode,
        filters=graphene.Argument(graphene.JSONString)
    )

    def resolve_cg_cable_gland_model_lines(self, info, filters=None, **kwargs):
        qs = CableGlandModelLine.objects.all()

        if not filters:
            return qs

        query = Q()

        # Текстовый поиск
        if 'search' in filters:
            query &= Q(symbolic_code__icontains=filters['search'])

        # Фильтры по связанным полям
        if 'brand_name' in filters:
            query &= Q(brand__name__icontains=filters['brand_name'])
        if 'cable_gland_type_name' in filters:
            query &= Q(cable_gland_type__name__icontains=filters['cable_gland_type_name'])

        # Точные совпадения
        if 'symbolic_code' in filters:
            query &= Q(symbolic_code=filters['symbolic_code'])

        # Булевы поля
        bool_fields = [
            'for_armored_cable',
            'for_metal_sleeve_cable',
            'for_pipelines_cable'
        ]
        for field in bool_fields:
            if field in filters:
                query &= Q(**{field: filters[field]})

        return qs.filter(query)

    def resolve_cg_cable_gland_items(self, info, filters=None, **kwargs):
        qs = CableGlandItem.objects.all()

        if not filters:
            return qs

        query = Q()

        # Текстовый поиск
        if 'search' in filters:
            query &= Q(name__icontains=filters['search'])
        if 'model_line_code' in filters:
            query &= Q(model_line__symbolic_code__icontains=filters['model_line_code'])
        if 'material_name' in filters:
            query &= Q(cable_gland_body_material__name__icontains=filters['material_name'])

        # Точные совпадения
        if 'name' in filters:
            query &= Q(name=filters['name'])
        if 'exd_same_as_model_line' in filters:
            query &= Q(exd_same_as_model_line=filters['exd_same_as_model_line'])

        # Числовые диапазоны
        if 'temp_min' in filters:
            if isinstance(filters['temp_min'], dict):
                if 'gte' in filters['temp_min']:
                    query &= Q(temp_min__gte=filters['temp_min']['gte'])
                if 'lte' in filters['temp_min']:
                    query &= Q(temp_min__lte=filters['temp_min']['lte'])
            else:
                query &= Q(temp_min=filters['temp_min'])

        if 'temp_max' in filters:
            if isinstance(filters['temp_max'], dict):
                if 'gte' in filters['temp_max']:
                    query &= Q(temp_max__gte=filters['temp_max']['gte'])
                if 'lte' in filters['temp_max']:
                    query &= Q(temp_max__lte=filters['temp_max']['lte'])
            else:
                query &= Q(temp_max=filters['temp_max'])

        return qs.filter(query)