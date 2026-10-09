# pneumatic_fittings/filters.py
from core.models.smart_catalog_mixin import FilterDefinition , FilterType , DataSourceType
from params.models import ThreadTypes

# Общие фильтры (бренд/серия/корпус/резьба/температура) для трёх видов.
_COMMON_FILTER_DEFINITIONS = [
        FilterDefinition(
            param_name='brand_id' ,
            model_field='model_line__brand' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Бренд' ,
            order=1
        ) ,
        FilterDefinition(
            param_name='model_line_id' ,
            model_field='model_line' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Серия' ,
            order=2
        ) ,
        FilterDefinition(
            param_name='body_material_id' ,
            model_field='body_material' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Материал корпуса' ,
            order=3
        ) ,
        FilterDefinition(
            param_name='thread_type_id' ,
            model_field='thread' ,
            is_parent_filter=True ,
            filter_type=FilterType.THREAD_COMPATIBLE ,
            data_source_type=DataSourceType.GLOBAL_MODEL ,
            source_model=ThreadTypes ,
            label='Тип резьбы' ,
            order=4
        ) ,
        FilterDefinition(
            param_name='thread_id' ,
            model_field='thread' ,
            filter_type=FilterType.THREAD_COMPATIBLE ,
            data_source_type=DataSourceType.UNIQUE_FIELD_VALUES ,
            label='Резьба' ,
            order=5
        ) ,
        FilterDefinition(
            param_name='thread_inner_outer_id' ,
            model_field='thread_inner_outer' ,
            filter_type=FilterType.EXACT ,
            data_source_type=DataSourceType.FOREIGN_KEY ,
            label='Тип резьбы (нар/внут)' ,
            order=6
        ) ,
        FilterDefinition(
            param_name='temp_min' ,
            model_field='model_line__temp_min' ,
            filter_type=FilterType.TEMP_MIN ,
            data_source_type=DataSourceType.FIELD_VALUES ,
            label='Мин. температура (≤)' ,
            order=7
        ) ,
        FilterDefinition(
            param_name='pressure_min' ,
            model_field='model_line__pressure_min' ,
            filter_type=FilterType.MAX ,
            data_source_type=DataSourceType.FIELD_VALUES ,
            label='P раб.мин не более, бар' ,
            order=8
        ) ,
        FilterDefinition(
            param_name='pressure_max' ,
            model_field='model_line__pressure_max' ,
            filter_type=FilterType.MIN ,
            data_source_type=DataSourceType.FIELD_VALUES ,
            label='P раб.макс не менее, бар' ,
            order=9
        ) ,
    ]

