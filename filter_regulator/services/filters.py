# filter_regulator/services/filters.py
"""
Фильтры для каталога фильтр-регуляторов.
"""
from core.models.smart_catalog_mixin import FilterDefinition, FilterType, DataSourceType
from params.models import IpOption


FILTER_REGULATOR_FILTER_DEFINITIONS = [
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
    # Бренд через серию
    FilterDefinition(
        param_name='brand_id',
        model_field='model_line__brand',
        filter_type=FilterType.EXACT,
        data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
        label='Бренд',
        order=10,
    ),
]

FILTER_REGULATOR_SEARCH_FIELDS = ['code', 'name', 'description']

FILTER_REGULATOR_SELECT_RELATED = [
    'model_line',
    'model_line__brand',
    'model_line__filter_variety',
    'body',
    'body__thread',
    'body__gauge_port_size',
    'body__drain_port_size',
    'ip',
    'body_material',
    'sku',
]

FILTER_REGULATOR_PREFETCH_FIELDS = [
    'images',
    'tech_docs',
    'model_line__images',
    'model_line__tech_docs',
]
