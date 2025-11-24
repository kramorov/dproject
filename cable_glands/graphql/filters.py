from graphene_django.filter import DjangoFilterConnectionField
from django_filters import FilterSet, CharFilter, BooleanFilter  # Import from django_filters

from cable_glands.graphql.types import DescriptionItemType , CableGlandModelLineNode , CableGlandItemNode
from cable_glands.models import CableGlandModelLine, CableGlandItem

class CableGlandModelLineFilter(FilterSet):
    symbolic_code = CharFilter(lookup_expr='exact')
    symbolic_code_contains = CharFilter(field_name='symbolic_code' , lookup_expr='contains')

    brand_name = CharFilter(field_name='brand__name' , lookup_expr='exact')
    brand_name_contains = CharFilter(field_name='brand__name' , lookup_expr='contains')

    cable_gland_type_name = CharFilter(field_name='cable_gland_type__name' , lookup_expr='exact')
    cable_gland_type_name_contains = CharFilter(field_name='cable_gland_type__name' , lookup_expr='contains')

    for_armored_cable = BooleanFilter()
    for_metal_sleeve_cable = BooleanFilter()
    for_pipelines_cable = BooleanFilter()

    class Meta :
        model = CableGlandModelLine
        fields = []

class CableGlandItemFilter(FilterSet):
    class Meta:
        model = CableGlandItem
        fields = {
            'name': ['exact', 'contains'],
            'model_line__symbolic_code': ['exact', 'contains'],
            'cable_gland_body_material__name': ['exact', 'contains'],
            'exd_same_as_model_line': ['exact'],
            'temp_min': ['exact', 'gte', 'lte'],
            'temp_max': ['exact', 'gte', 'lte'],
        }