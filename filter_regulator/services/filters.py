# filter_regulator/services/filters.py
"""
Фильтры для каталога фильтр-регуляторов.
"""
from core.models.smart_catalog_mixin import FilterDefinition, FilterType, DataSourceType


FILTER_REGULATOR_FILTER_DEFINITIONS = [
    # Серия (model_line) — главный фильтр
    FilterDefinition(
        param_name='model_line_id',
        model_field='model_line',
        filter_type=FilterType.EXACT,
        data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
        label='Серия',
        order=1,
    ),
    # Тонкость фильтрации
    FilterDefinition(
        param_name='filtration_rating_min',
        model_field='filtration_rating',
        filter_type=FilterType.MIN,
        data_source_type=DataSourceType.FIELD_VALUES,
        label='Тонкость фильтрации, мкм',
        order=2,
    ),
    # Материал корпуса
    FilterDefinition(
        param_name='body_material_id',
        model_field='body_material',
        filter_type=FilterType.EXACT,
        data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
        label='Материал корпуса',
        order=3,
    ),
    # Расход
    FilterDefinition(
        param_name='flow_rate_min',
        model_field='flow_rate',
        filter_type=FilterType.MIN,
        data_source_type=DataSourceType.FIELD_VALUES,
        label='Расход не менее, л/мин',
        order=4,
    ),
    # Резьба портов
    FilterDefinition(
        param_name='thread_id',
        model_field='body__thread',
        filter_type=FilterType.EXACT,
        data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
        label='Резьба портов',
        order=5,
    ),
    # Температура мин
    FilterDefinition(
        param_name='work_temp_min',
        model_field='work_temp_min',
        filter_type=FilterType.TEMP_MIN,
        data_source_type=DataSourceType.FIELD_VALUES,
        label='Температура от, °С',
        order=6,
    ),
    # Температура макс
    FilterDefinition(
        param_name='work_temp_max',
        model_field='work_temp_max',
        filter_type=FilterType.TEMP_MAX,
        data_source_type=DataSourceType.FIELD_VALUES,
        label='Температура до, °С',
        order=7,
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
]

FILTER_REGULATOR_PREFETCH_FIELDS = [
    'images',
    'tech_docs',
    'model_line__images',
    'model_line__tech_docs',
    'model_line__cert_docs',
]

# Фильтры для быстрого подбора (QuickSelect)
QUICKSELECT_FILTERS = [
    'filtration_rating_min',
    'body_material_id',
    'flow_rate_min',
    'thread_id',
]