# cable_glands/catalog/filter_defs.py
"""FilterDefinition objects for the cable glands catalog.

Паттерн — solenoid_valves/catalog/filter_defs.py. Источник правды для
фильтров каталога и мастера подбора (Selection Wizard).
"""
from core.models.filter_definition import FilterDefinition, FilterType, DataSourceType
from params.models import IpOption, ThreadSize
from cable_glands.models import CableGlandBodyMaterial, CableType


# ── Individual filter definitions ──

fd_model_line = FilterDefinition(
    param_name='model_line_id',
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

fd_thread = FilterDefinition(
    param_name='thread_id',
    model_field='thread_option__thread_size',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    source_model=ThreadSize,
    label='Резьба',
    order=3,
)

fd_body_material = FilterDefinition(
    param_name='body_material_id',
    model_field='body_material_option__body_material',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    source_model=CableGlandBodyMaterial,
    label='Материал корпуса',
    order=4,
)

fd_exd = FilterDefinition(
    param_name='exd_id',
    model_field='exd_option__exd_options',
    filter_type=FilterType.EXD_COMPATIBLE,          # frontend: ExdFilter (каскад)
    parameter_rule_code='exd',                      # backend: ParameterRule (hierarchy)
    data_source_type=DataSourceType.CUSTOM,
    label='Взрывозащита',
    order=5,
)

fd_ip = FilterDefinition(
    param_name='ip_id',
    model_field='model_line__ip',
    filter_type=FilterType.EXACT,
    parameter_rule_code='ip',                       # backend: ParameterRule (subset по ip_rank)
    data_source_type=DataSourceType.GLOBAL_MODEL,
    source_model=IpOption,
    label='IP',
    order=6,
)

# Диаметр кабеля: «от» = gland.clamp_min <= value (ввод обожмёт этот кабель),
# «до» = gland.clamp_max >= value.
fd_cable_diameter_min = FilterDefinition(
    param_name='cable_diameter_min',
    model_field='model_line_item__body__cable_diameter_inner_min',
    filter_type=FilterType.MAX,                     # lte: inner_min <= value
    data_source_type=DataSourceType.CUSTOM,         # numeric input (no dropdown)
    label='Кабель от, мм',
    order=7,
)

fd_cable_diameter_max = FilterDefinition(
    param_name='cable_diameter_max',
    model_field='model_line_item__body__cable_diameter_inner_max',
    filter_type=FilterType.MIN,                     # gte: inner_max >= value
    data_source_type=DataSourceType.CUSTOM,         # numeric input (no dropdown)
    label='Кабель до, мм',
    order=8,
)

fd_cable_diameter_outer_min = FilterDefinition(
    param_name='cable_diameter_outer_min',
    model_field='model_line_item__cable_diameter_outer_min',
    filter_type=FilterType.MAX,                     # lte: outer_min <= value
    data_source_type=DataSourceType.CUSTOM,         # numeric input (no dropdown)
    label='Броня от, мм',
    order=9,
)

fd_cable_diameter_outer_max = FilterDefinition(
    param_name='cable_diameter_outer_max',
    model_field='model_line_item__cable_diameter_outer_max',
    filter_type=FilterType.MIN,                     # gte: outer_max >= value
    data_source_type=DataSourceType.CUSTOM,         # numeric input (no dropdown)
    label='Броня до, мм',
    order=10,
)

fd_temp_min = FilterDefinition(
    param_name='work_temp_min',
    model_field='model_line__temp_min',
    filter_type=FilterType.TEMP_MIN,
    parameter_rule_code='temperature_min',          # backend: ParameterRule (directional)
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Температура от, °С',
    order=11,
)

fd_temp_max = FilterDefinition(
    param_name='work_temp_max',
    model_field='model_line__temp_max',
    filter_type=FilterType.TEMP_MAX,
    parameter_rule_code='temperature_max',          # backend: ParameterRule (directional)
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Температура до, °С',
    order=12,
)

fd_climate = FilterDefinition(
    param_name='climate',
    model_field='model_line__temp_min',
    filter_type=FilterType.CLIMATE_CASCADE,     # frontend: ClimateFilter (слайдер климата)
    data_source_type=DataSourceType.CUSTOM,
    label='Клим. исполнение',
    order=50,
)

# ── Тип кабеля (справочник CableType; заменяет булевы флаги серии) ──

fd_cable_type = FilterDefinition(
    param_name='cable_type_id',
    model_field='model_line__cable_type',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    source_model=CableType,
    label='Тип кабеля',
    order=13,
)


# ── Legacy flat list (для мастера подбора / AI) ──

CABLE_GLAND_FILTER_DEFINITIONS = [
    fd_model_line,
    fd_brand,
    fd_thread,
    fd_body_material,
    fd_exd,
    fd_ip,
    fd_cable_diameter_min,
    fd_cable_diameter_max,
    fd_cable_diameter_outer_min,
    fd_cable_diameter_outer_max,
    fd_temp_min,
    fd_temp_max,
    fd_climate,
    fd_cable_type,
]
