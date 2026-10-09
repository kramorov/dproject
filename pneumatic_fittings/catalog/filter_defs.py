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
    param_name='model_line_id',
    model_field='model_line',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Серия',
    label_i18n={'en': 'Series', 'cn': '系列'},
    order=1,
)

fd_brand = FilterDefinition(
    param_name='brand_id',
    model_field='model_line__brand',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Бренд',
    label_i18n={'en': 'Brand', 'cn': '品牌'},
    order=2,
)

fd_shape = FilterDefinition(
    param_name='shape_id',
    model_field='model_line__shape',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Форма фитинга',
    label_i18n={'en': 'Fitting shape', 'cn': '接头形状'},
    order=3,
)

fd_fixation_method = FilterDefinition(
    param_name='fixation_method_id',
    model_field='model_line__fixation_method',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Способ фиксации',
    label_i18n={'en': 'Fixation method', 'cn': '固定方式'},
    order=4,
)

fd_body_material = FilterDefinition(
    param_name='body_material_id',
    model_field='body_material',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    source_model=MaterialGeneral,
    label='Материал корпуса',
    label_i18n={'en': 'Body material', 'cn': '壳体材料'},
    order=4,
)

fd_pipe_material = FilterDefinition(
    param_name='pipe_material_id',
    model_field='pipe_material',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    source_model=MaterialGeneral,
    label='Материал трубки',
    label_i18n={'en': 'Tube material', 'cn': '气管材料'},
    order=5,
)

fd_pipe_diameter = FilterDefinition(
    param_name='pipe_diameter',
    model_field='pipe_diameter',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Диаметр трубки, мм',
    label_i18n={'en': 'Tube diameter, mm', 'cn': '气管直径, mm'},
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
    label_i18n={'en': 'Thread type', 'cn': '螺纹类型'},
    order=7,
)

fd_thread = FilterDefinition(
    param_name='thread_id',
    model_field='thread',
    filter_type=FilterType.THREAD_COMPATIBLE,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Резьба',
    label_i18n={'en': 'Thread', 'cn': '螺纹'},
    order=8,
)

fd_thread_inner_outer = FilterDefinition(
    param_name='thread_inner_outer_id',
    model_field='thread_inner_outer',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.FOREIGN_KEY,
    source_model=ThreadInnerOuter,
    label='Резьба (нар/внут)',
    label_i18n={'en': 'Thread (ext/int)', 'cn': '螺纹（外/内）'},
    order=9,
)

fd_temp_min = FilterDefinition(
    param_name='temp_min',
    model_field='model_line__temp_min',
    filter_type=FilterType.TEMP_MIN,            # frontend: temperature slider
    parameter_rule_code='temperature_min',      # backend: ParameterRule
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Температура от, °С',
    label_i18n={'en': 'Temperature from, °C', 'cn': '最低温度, °C'},
    order=10,
)


fd_pressure_min = FilterDefinition(
    param_name='pressure_min',
    model_field='model_line__pressure_min',
    filter_type=FilterType.MAX,                 # lte: "не более X бар"
    data_source_type=DataSourceType.FIELD_VALUES,
    label='P раб.мин не более, бар',
    label_i18n={'en': 'Min. pressure max., bar', 'cn': '最小压力不高于, bar'},
    order=11,
)


fd_pressure_max = FilterDefinition(
    param_name='pressure_max',
    model_field='model_line__pressure_max',
    filter_type=FilterType.MIN,                 # gte: "не менее X бар"
    data_source_type=DataSourceType.FIELD_VALUES,
    label='P раб.макс не менее, бар',
    label_i18n={'en': 'Max. pressure min., bar', 'cn': '最大压力不低于, bar'},
    order=12,
)


fd_swivel = FilterDefinition(
    param_name='swivel',
    model_field='model_line__is_swivel',
    filter_type=FilterType.BOOLEAN,
    data_source_type=DataSourceType.CHOICES,
    choices=[('true', 'Поворотный'), ('false', 'Неповоротный')],
    label='Поворотность',
    label_i18n={'en': 'Swivel', 'cn': '可旋转'},
    order=13,
)


# ── Legacy flat list ──

PNEUMATIC_FITTINGS_FILTER_DEFINITIONS = [
    fd_model_line,
    fd_brand,
    fd_shape,
    fd_fixation_method,
    fd_body_material,
    fd_pipe_material,
    fd_pipe_diameter,
    fd_thread_type,
    fd_thread,
    fd_thread_inner_outer,
    fd_temp_min,
    fd_pressure_min,
    fd_pressure_max,
    fd_swivel,
]
