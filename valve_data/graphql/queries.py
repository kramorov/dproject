# valve_data/graphql/queries.py
import graphene
from graphene_django import DjangoConnectionField
from django.core.paginator import Paginator
from django.db.models import Q

from .types import ValveModelDataResult , PageInfo , ValveLineModelDataNode , ValveLineNode , ValveLineFilterInput
from producers.graphql.types import ProducerNode , BrandsNode
from valve_data.models import ValveLine
from producers.models import Producer


class ValveLineQuery(graphene.ObjectType) :
    valve_lines = graphene.List(
        ValveLineNode ,
        filters=ValveLineFilterInput() ,
        first=graphene.Int() ,
        skip=graphene.Int()
    )
    valve_line = graphene.Field(ValveLineNode , id=graphene.ID(required=True))

    def resolve_valve_lines(self , info , filters=None , first=None , skip=None , **kwargs) :
        queryset = ValveLine.objects.all()

        if filters :
            # Фильтрация по эффективным строковым значениям через геттеры
            string_filters = {
                'valve_producer' : 'effective_valve_producer_str' ,
                'valve_brand' : 'effective_valve_brand_str' ,
                'valve_variety' : 'effective_valve_variety_str' ,
                'valve_function' : 'effective_valve_function_str' ,
                'valve_actuation' : 'effective_valve_actuation_str' ,
                'valve_sealing_class' : 'effective_valve_sealing_class_str' ,
                'body_material' : 'effective_body_material_str' ,
                'body_material_specified' : 'effective_body_material_specified_str' ,
                'shut_element_material' : 'effective_shut_element_material_str' ,
                'shut_element_material_specified' : 'effective_shut_element_material_specified_str' ,
                'sealing_element_material' : 'effective_sealing_element_material_str' ,
                'sealing_element_material_specified' : 'effective_sealing_element_material_specified_str' ,
            }

            # Применяем фильтры по эффективным значениям
            for filter_field , getter_name in string_filters.items() :
                if getattr(filters , filter_field , None) :
                    filter_values = getattr(filters , filter_field)
                    # Фильтруем в Python, так как эффективные значения вычисляются в коде
                    filtered_ids = []
                    for valve_line in queryset :
                        effective_value = getattr(valve_line , getter_name , None)
                        if effective_value and effective_value in filter_values :
                            filtered_ids.append(valve_line.id)
                    queryset = queryset.filter(id__in=filtered_ids)

            # Числовые фильтры по эффективным значениям
            if hasattr(filters , 'work_temp_min__gte') and filters.work_temp_min__gte is not None :
                filtered_ids = [
                    vl.id for vl in queryset
                    if vl.effective_work_temp_min and vl.effective_work_temp_min >= filters.work_temp_min__gte
                ]
                queryset = queryset.filter(id__in=filtered_ids)

            if hasattr(filters , 'work_temp_min__lte') and filters.work_temp_min__lte is not None :
                filtered_ids = [
                    vl.id for vl in queryset
                    if vl.effective_work_temp_min and vl.effective_work_temp_min <= filters.work_temp_min__lte
                ]
                queryset = queryset.filter(id__in=filtered_ids)

            if hasattr(filters , 'work_temp_max__gte') and filters.work_temp_max__gte is not None :
                filtered_ids = [
                    vl.id for vl in queryset
                    if vl.effective_work_temp_max and vl.effective_work_temp_max >= filters.work_temp_max__gte
                ]
                queryset = queryset.filter(id__in=filtered_ids)

            if hasattr(filters , 'work_temp_max__lte') and filters.work_temp_max__lte is not None :
                filtered_ids = [
                    vl.id for vl in queryset
                    if vl.effective_work_temp_max and vl.effective_work_temp_max <= filters.work_temp_max__lte
                ]
                queryset = queryset.filter(id__in=filtered_ids)

            # Точные фильтры по эффективным значениям
            if filters.port_qty :
                filtered_ids = [
                    vl.id for vl in queryset
                    if vl.effective_port_qty_str and vl.effective_port_qty_str == filters.port_qty
                ]
                queryset = queryset.filter(id__in=filtered_ids)

            if filters.construction_variety :
                filtered_ids = [
                    vl.id for vl in queryset
                    if
                    vl.effective_construction_variety_str and vl.effective_construction_variety_str == filters.construction_variety
                ]
                queryset = queryset.filter(id__in=filtered_ids)

            # Фильтр по DN через allowed_dn_table (используем эффективное значение)
            if filters.allowed_dn :
                filtered_ids = [
                    vl.id for vl in queryset
                    if vl.effective_allowed_dn_table_str and filters.allowed_dn in vl.effective_allowed_dn_table_str
                ]
                queryset = queryset.filter(id__in=filtered_ids)

            # Поиск по названию и коду (используем эффективные значения)
            if filters.search :
                search_term = filters.search.lower()
                filtered_ids = []
                for valve_line in queryset :
                    # Ищем в эффективных названиях и кодах
                    if (valve_line.effective_name and search_term in valve_line.effective_name.lower()) or \
                            (valve_line.effective_code and search_term in valve_line.effective_code.lower()) or \
                            (
                                    valve_line.effective_description and search_term in valve_line.effective_description.lower()) :
                        filtered_ids.append(valve_line.id)
                queryset = queryset.filter(id__in=filtered_ids)

            # Фильтры по статусу (прямые поля модели)
            if hasattr(filters , 'is_active') and filters.is_active is not None :
                queryset = queryset.filter(is_active=filters.is_active)
            if hasattr(filters , 'is_approved') and filters.is_approved is not None :
                queryset = queryset.filter(is_approved=filters.is_approved)

        # Пагинация
        if skip :
            queryset = queryset[skip :]
        if first :
            queryset = queryset[:first]

        return queryset

    def resolve_valve_line(self , info , id) :
        return ValveLine.objects.get(id=id)


class Query(ValveLineQuery , graphene.ObjectType) :
    pass