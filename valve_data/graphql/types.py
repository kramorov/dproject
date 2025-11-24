# valve_data/graphql/types.py
import graphene
from graphene_django import DjangoObjectType
from valve_data.models import ValveLineModelData , ValveLine
from producers.graphql.types import ProducerNode , BrandsNode
from params.graphql.types import ValveTypesNode , MeasureUnitsNode , StemSizeNode , MountingPlateTypesNode
from typing import Optional
# Импортируем модель DnVariety
from params.models import DnVariety

class AllowedDnNode(DjangoObjectType) :
    class Meta :
        model = DnVariety  # Передаем класс модели, а не строку
        fields = ['id' , 'name' , 'code' , 'diameter_metric']


class BasicInfoNode(graphene.ObjectType) :
    key = graphene.String()
    label = graphene.String()
    value = graphene.String()


class TechnicalSpecsNode(graphene.ObjectType) :
    key = graphene.String()
    label = graphene.String()
    value = graphene.String()


class TemperatureInfoNode(graphene.ObjectType) :
    key = graphene.String()
    label = graphene.String()
    value = graphene.Int()


class BodyColorNode(graphene.ObjectType) :
    color_name = graphene.String()
    option_type = graphene.String()
    additional_cost = graphene.Float()
    lead_time_days = graphene.Int()
    option_code = graphene.String()
    hex_color = graphene.String()


class ServiceLifeInfoNode(graphene.ObjectType) :
    label = graphene.String()
    value = graphene.String()


class ValveLineNode(DjangoObjectType) :
    class Meta :
        model = ValveLine
        fields = "__all__"

    # Вычисляемые поля через геттеры
    basic_info = graphene.List(BasicInfoNode)
    technical_specs = graphene.List(TechnicalSpecsNode)
    temperature_info = graphene.List(TemperatureInfoNode)
    body_colors_info = graphene.List(BodyColorNode)
    service_life_info = graphene.List(ServiceLifeInfoNode)

    # Поля для фильтрации (эффективные значения)
    effective_valve_producer = graphene.String()
    effective_valve_brand = graphene.String()
    effective_valve_variety = graphene.String()
    effective_valve_function = graphene.String()
    effective_valve_actuation = graphene.String()
    effective_valve_sealing_class = graphene.String()
    effective_body_material = graphene.String()
    effective_body_material_specified = graphene.String()
    effective_shut_element_material = graphene.String()
    effective_shut_element_material_specified = graphene.String()
    effective_sealing_element_material = graphene.String()
    effective_sealing_element_material_specified = graphene.String()
    effective_work_temp_min = graphene.Int()
    effective_work_temp_max = graphene.Int()
    effective_port_qty = graphene.String()
    effective_construction_variety = graphene.String()
    effective_allowed_dn_table = graphene.String()

    # Boolean properties
    has_technical_data = graphene.Boolean()
    has_options = graphene.Boolean()
    has_kv_data = graphene.Boolean()
    has_dimension_data = graphene.Boolean()
    has_required_data = graphene.Boolean()

    def resolve_basic_info(self , info) :
        return self.get_basic_info()

    def resolve_technical_specs(self , info) :
        return self.get_technical_specs()

    def resolve_temperature_info(self , info) :
        return self.get_temperature_info()

    def resolve_body_colors_info(self , info) :
        return self.get_body_colors_info()

    def resolve_service_life_info(self , info) :
        return self.get_service_life_info()

    # Резолверы для эффективных значений
    def resolve_effective_valve_producer(self , info) :
        return self.effective_valve_producer_str

    def resolve_effective_valve_brand(self , info) :
        return self.effective_valve_brand_str

    def resolve_effective_valve_variety(self , info) :
        return self.effective_valve_variety_str

    def resolve_effective_valve_function(self , info) :
        return self.effective_valve_function_str

    def resolve_effective_valve_actuation(self , info) :
        return self.effective_valve_actuation_str

    def resolve_effective_valve_sealing_class(self , info) :
        return self.effective_valve_sealing_class_str

    def resolve_effective_body_material(self , info) :
        return self.effective_body_material_str

    def resolve_effective_body_material_specified(self , info) :
        return self.effective_body_material_specified_str

    def resolve_effective_shut_element_material(self , info) :
        return self.effective_shut_element_material_str

    def resolve_effective_shut_element_material_specified(self , info) :
        return self.effective_shut_element_material_specified_str

    def resolve_effective_sealing_element_material(self , info) :
        return self.effective_sealing_element_material_str

    def resolve_effective_sealing_element_material_specified(self , info) :
        return self.effective_sealing_element_material_specified_str

    def resolve_effective_work_temp_min(self , info) :
        return self.effective_work_temp_min

    def resolve_effective_work_temp_max(self , info) :
        return self.effective_work_temp_max

    def resolve_effective_port_qty(self , info) :
        return self.effective_port_qty_str

    def resolve_effective_construction_variety(self , info) :
        return self.effective_construction_variety_str

    def resolve_effective_allowed_dn_table(self , info) :
        return self.effective_allowed_dn_table_str

    # Резолверы для boolean properties
    def resolve_has_technical_data(self , info) :
        return self.has_technical_data

    def resolve_has_options(self , info) :
        return self.has_options

    def resolve_has_kv_data(self , info) :
        return self.has_kv_data

    def resolve_has_dimension_data(self , info) :
        return self.has_dimension_data

    def resolve_has_required_data(self , info) :
        return self.has_required_data


class ValveLineFilterInput(graphene.InputObjectType) :
    # Фильтры по эффективным значениям (строковые)
    valve_producer = graphene.List(graphene.String)
    valve_brand = graphene.List(graphene.String)
    valve_variety = graphene.List(graphene.String)
    valve_function = graphene.List(graphene.String)
    valve_actuation = graphene.List(graphene.String)
    valve_sealing_class = graphene.List(graphene.String)
    body_material = graphene.List(graphene.String)
    body_material_specified = graphene.List(graphene.String)
    shut_element_material = graphene.List(graphene.String)
    shut_element_material_specified = graphene.List(graphene.String)
    sealing_element_material = graphene.List(graphene.String)
    sealing_element_material_specified = graphene.List(graphene.String)

    # Числовые фильтры
    work_temp_min__gte = graphene.Int()
    work_temp_min__lte = graphene.Int()
    work_temp_max__gte = graphene.Int()
    work_temp_max__lte = graphene.Int()

    # Точный выбор
    port_qty = graphene.String()
    construction_variety = graphene.String()

    # Фильтр по DN
    allowed_dn = graphene.String()

    # Поиск
    search = graphene.String()
    is_active = graphene.Boolean()
    is_approved = graphene.Boolean()


class ValveLineModelDataNode(DjangoObjectType) :
    class Meta :
        model = ValveLineModelData
        interfaces = (graphene.relay.Node ,)
        fields = "__all__"

    # Явно объявляем поле связи с ValveLine
    valve_model_model_line = graphene.Field(ValveLineNode)

    # Объявляем кастомные поля, которые будут резолвиться через геттеры
    effective_valve_producer = graphene.Field(ProducerNode)
    effective_valve_brand = graphene.Field(BrandsNode)
    effective_valve_type = graphene.Field(ValveTypesNode)
    valve_model_pn_measure_unit = graphene.Field(MeasureUnitsNode)
    valve_model_stem_size = graphene.Field(StemSizeNode)
    valve_model_mounting_plate = graphene.List(MountingPlateTypesNode)

    def resolve_valve_model_model_line(self: ValveLineModelData , info) -> Optional[ValveLine] :
        return self.valve_model_line

    def resolve_effective_valve_producer(self: ValveLineModelData , info) -> Optional :
        # Используем геттер из ValveLine
        if self.valve_model_line :
            return self.valve_model_line.effective_valve_producer
        return None

    def resolve_effective_valve_brand(self: ValveLineModelData , info) -> Optional :
        # Используем геттер из ValveLine
        if self.valve_model_line :
            return self.valve_model_line.effective_valve_brand
        return None

    def resolve_effective_valve_type(self: ValveLineModelData , info) -> Optional :
        # Используем геттер из ValveLine
        if self.valve_model_line :
            return self.valve_model_line.effective_valve_variety
        return None

    def resolve_valve_model_stem_size(self: ValveLineModelData , info) -> Optional :
        return self.valve_model_stem_size

    def resolve_valve_model_mounting_plate(self: ValveLineModelData , info) -> list :
        if hasattr(self , 'valve_model_mounting_plate') :
            return self.valve_model_mounting_plate.all()
        return []


class PageInfo(graphene.ObjectType) :
    has_next_page = graphene.Boolean()
    has_previous_page = graphene.Boolean()
    current_page = graphene.Int()
    total_pages = graphene.Int()


class ValveModelDataResult(graphene.ObjectType) :
    items = graphene.List(ValveLineModelDataNode)
    total_count = graphene.Int()
    page_info = graphene.Field(PageInfo)