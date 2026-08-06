# filter_regulator/catalog/filter_defs.py
"""
FilterDefinition objects for the filter-regulator catalog.
"""
from core.models.filter_definition import FilterDefinition, FilterType, DataSourceType

# ── Individual filter definitions ──

fd_model_line = FilterDefinition(
    param_name='model_line_id',
    model_field='model_line',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Серия',
    order=1,
)

fd_filtration = FilterDefinition(
    param_name='filtration_rating_min',
    model_field='filtration_rating',
    filter_type=FilterType.MIN,
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Тонкость фильтрации, мкм',
    order=2,
)

fd_body_material = FilterDefinition(
    param_name='body_material_id',
    model_field='body_material',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Материал корпуса',
    order=3,
)

fd_flow_rate = FilterDefinition(
    param_name='flow_rate_min',
    model_field='flow_rate',
    filter_type=FilterType.MIN,
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Расход не менее, л/мин',
    order=4,
)

fd_thread = FilterDefinition(
    param_name='thread_id',
    model_field='body__thread',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Резьба портов',
    order=5,
)

fd_thread_type = FilterDefinition(
    param_name="thread_type_id",
    model_field="body__thread__thread_type",
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label="Тип резьбы",
    order=6,
    is_parent_filter=True,
)

fd_temp_min = FilterDefinition(
    param_name='work_temp_min',
    model_field='work_temp_min',
    filter_type=FilterType.TEMP_MIN,
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Температура от, °С',
    order=6,
)

fd_temp_max = FilterDefinition(
    param_name='work_temp_max',
    model_field='work_temp_max',
    filter_type=FilterType.TEMP_MAX,
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Температура до, °С',
    order=7,
)

fd_climate = FilterDefinition(
    param_name='climate',
    model_field='work_temp_min',
    filter_type=FilterType.CLIMATE_CASCADE,
    data_source_type=DataSourceType.CUSTOM,
    label='Клим. исполнение',
    order=8,
)

fd_brand = FilterDefinition(
    param_name='brand_id',
    model_field='model_line__brand',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Бренд',
    order=10,
)

# ── Legacy flat list ──

FILTER_REGULATOR_FILTER_DEFINITIONS = [
    fd_model_line,
    fd_filtration,
    fd_body_material,
    fd_flow_rate,
    fd_thread,
    fd_temp_min,
    fd_temp_max,
    fd_climate,
    fd_brand,
]