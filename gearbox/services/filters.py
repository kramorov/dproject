# gearbox/services/filters.py
"""
Фильтры для каталога редукторов — вынесены из модели GearBox.
Используются вьюхой каталога для построения фильтров и опций.
"""
from core.models.smart_catalog_mixin import FilterDefinition, FilterType, DataSourceType
from params.models import IpOption


GEARBOX_FILTER_DEFINITIONS = [
    # IP (с ранжированием)
    FilterDefinition(
        param_name='ip_id',
        model_field='ip',
        filter_type=FilterType.IP_RANK,
        data_source_type=DataSourceType.GLOBAL_MODEL,
        source_model=IpOption,
        label='IP',
        order=4,
    ),
    # Температура мин
    FilterDefinition(
        param_name='work_temp_min',
        model_field='work_temp_min',
        filter_type=FilterType.TEMP_MIN,
        data_source_type=DataSourceType.FIELD_VALUES,
        label='Температура от, °С',
        order=5,
    ),
    # Температура макс
    FilterDefinition(
        param_name='work_temp_max',
        model_field='work_temp_max',
        filter_type=FilterType.TEMP_MAX,
        data_source_type=DataSourceType.FIELD_VALUES,
        label='Температура до, °С',
        order=6,
    ),
    # Рабочий момент не меньше
    FilterDefinition(
        param_name='min_work_torque',
        model_field='body__max_work_torque',
        filter_type=FilterType.MIN,
        data_source_type=DataSourceType.FIELD_VALUES,
        label='Рабочий момент не менее, Нм',
        order=7,
    ),
    # Материал корпуса — только используемые в GearBox
    FilterDefinition(
        param_name='body_material_id',
        model_field='body_material',
        filter_type=FilterType.EXACT,
        data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
        label='Материал корпуса',
        order=8,
    ),
    # Бренд через серию
    FilterDefinition(
        param_name='brand_id',
        model_field='model_line__brand',
        filter_type=FilterType.EXACT,
        data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
        label='Бренд',
        order=10,
    ),
    # Монтажная площадка — только используемые в GearBox
    FilterDefinition(
        param_name='mounting_plate_top_id',
        model_field='body__mounting_plate_top',
        filter_type=FilterType.EXACT,
        data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
        label='Монтажная площадка',
        order=11,
    ),
]

# M2M-фильтры: связь параметр запроса → поле модели
GEARBOX_M2M_FILTER_CONFIG = [
    {
        'param_name': 'mounting_plate_top_id',
        'm2m_field': 'body__mounting_plate_top',
    },
]

GEARBOX_SEARCH_FIELDS = ['code', 'name', 'description']

GEARBOX_SELECT_RELATED = [
    'model_line',
    'model_line__brand',
    'model_line__gearbox_output_variety',
    'model_line__gearbox_variety',
    'body',
    'body__transmission_variety',
    'ip',
    'body_material',
    'sku',
]

GEARBOX_PREFETCH_FIELDS = [
    'images',
    'tech_docs',
    'model_line__images',
    'model_line__tech_docs',
    'model_line__cert_docs',
    'body__mounting_plate_top',
    'body__mounting_plate_bottom',
]
