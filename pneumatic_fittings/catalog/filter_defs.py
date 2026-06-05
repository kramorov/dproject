# pneumatic_fittings/catalog/filter_defs.py
"""
FilterDefinition objects for pneumatic fittings catalog.
"""
from core.models.filter_definition import FilterDefinition, FilterType, DataSourceType
from materials.models import MaterialGeneral
from params.models import ThreadInnerOuter, ThreadTypes, ThreadSize
from producers.models import Brands


# ── Individual filter definitions ──

fd_model_line = FilterDefinition(
    param_name='fitting_model_line_id',
    model_field='model_line',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Серия',
    order=1,
)

fd_brand = FilterDefinition(
    param_name='brand_id',
    model_field='model_line__brand',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Бренд',
    order=2,
)

fd_fitting_variety = FilterDefinition(
    param_name='fitting_variety_id',
    model_field='fitting_variety',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Тип фитинга',
    order=3,
)

fd_body_material = FilterDefinition(
    param_name='body_material_id',
    model_field='body_material',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    source_model=MaterialGeneral,
    label='Материал корпуса',
    order=4,
)

fd_pipe_material = FilterDefinition(
    param_name='pipe_material_id',
    model_field='pipe_material',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    source_model=MaterialGeneral,
    label='Материал трубки',
    order=5,
)

fd_pipe_diameter = FilterDefinition(
    param_name='pipe_diameter',
    model_field='pipe_diameter',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Диаметр трубки, мм',
    order=6,
)

fd_thread_type = FilterDefinition(
    param_name='thread_type_id',
    model_field='thread',
    is_parent_filter=True,
    filter_type=FilterType.THREAD_COMPATIBLE,
    data_source_type=DataSourceType.GLOBAL_MODEL,
    source_model=ThreadTypes,
    label='Тип резьбы',
    order=7,
)

fd_thread = FilterDefinition(
    param_name='thread_id',
    model_field='thread',
    filter_type=FilterType.THREAD_COMPATIBLE,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Резьба',
    order=8,
)

fd_thread_inner_outer = FilterDefinition(
    param_name='thread_inner_outer_id',
    model_field='thread_inner_outer',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.FOREIGN_KEY,
    source_model=ThreadInnerOuter,
    label='Резьба (нар/внут)',
    order=9,
)

fd_temp_min = FilterDefinition(
    param_name='temp_min',
    model_field='temp_min',
    filter_type=FilterType.TEMP_MIN,
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Температура от, °С',
    order=10,
)


# ── Legacy flat list ──

PNEUMATIC_FITTINGS_FILTER_DEFINITIONS = [
    fd_model_line,
    fd_brand,
    fd_fitting_variety,
    fd_body_material,
    fd_pipe_material,
    fd_pipe_diameter,
    fd_thread_type,
    fd_thread,
    fd_thread_inner_outer,
    fd_temp_min,
]
