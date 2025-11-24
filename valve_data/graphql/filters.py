# valve_data/graphql/filters.py
import django_filters
from django.db.models import Q
from valve_data.models import ValveModelData
from valve_data.models_valve_line import ValveLine
from producers.models import Producer, Brands
from params.models import ValveTypes


class ValveModelDataFilter(django_filters.FilterSet):
    valve_producer_id = django_filters.NumberFilter(field_name='valve_model_model_line__valve_producer__id')
    valve_brand_id = django_filters.NumberFilter(field_name='valve_model_model_line__valve_brand__id')
    valve_type_id = django_filters.NumberFilter(field_name='valve_model_model_line__valve_type__id')
    valve_model_dn = django_filters.NumberFilter(field_name='valve_model_dn')
    valve_model_pn = django_filters.NumberFilter(field_name='valve_model_pn')
    valve_model_pn_measure_unit_id = django_filters.NumberFilter(field_name='valve_model_pn_measure_unit__id')

    class Meta:
        model = ValveModelData
        fields = [
            'valve_producer_id', 'valve_brand_id', 'valve_type_id',
            'valve_model_dn', 'valve_model_pn', 'valve_model_pn_measure_unit_id'
        ]


class ValveLineFilter(django_filters.FilterSet):
    valve_type_id = django_filters.NumberFilter(field_name='valve_type__id')

    class Meta:
        model = ValveLine
        fields = ['valve_type_id']