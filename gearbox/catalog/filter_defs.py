# gearbox/catalog/filter_defs.py
"""
FilterDefinition objects for the gearbox catalog.

These are the same FilterDefinitions previously in gearbox/services/filters.py.
Kept here for the CatalogConfig; the old location remains for backward compat.
"""
from core.models.filter_definition import FilterDefinition, FilterType, DataSourceType
from params.models import IpOption

# ── Individual filter definitions (named for reuse in FilterSets) ──

fd_model_line = FilterDefinition(
    param_name='model_line_id',
    model_field='model_line',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Серия',
    label_i18n={'en': 'Series', 'cn': '系列'},
    order=1,
)

fd_ip = FilterDefinition(
    param_name='ip_id',
    model_field='ip',
    filter_type=FilterType.IP_RANK,            # frontend: IP rank UI
    parameter_rule_code='ip',                  # backend: ParameterRule 'ip'
    data_source_type=DataSourceType.GLOBAL_MODEL,
    source_model=IpOption,
    label='IP',
    label_i18n={'en': 'IP', 'cn': 'IP'},
    order=4,
)

fd_temp_min = FilterDefinition(
    param_name='work_temp_min',
    model_field='work_temp_min',
    filter_type=FilterType.TEMP_MIN,            # frontend: temperature slider
    parameter_rule_code='temperature_min',      # backend: ParameterRule
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Температура от, °С',
    label_i18n={'en': 'Temperature from, °C', 'cn': '最低温度, °C'},
    order=5,
)

fd_temp_max = FilterDefinition(
    param_name='work_temp_max',
    model_field='work_temp_max',
    filter_type=FilterType.TEMP_MAX,            # frontend: temperature slider
    parameter_rule_code='temperature_max',      # backend: ParameterRule
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Температура до, °С',
    label_i18n={'en': 'Temperature up to, °C', 'cn': '最高温度, °C'},
    order=6,
)

fd_climate = FilterDefinition(
    param_name='climate',
    model_field='work_temp_min',
    filter_type=FilterType.CLIMATE_CASCADE,
    data_source_type=DataSourceType.CUSTOM,
    label='Клим. исполнение',
    label_i18n={'en': 'Climate version', 'cn': '气候型式'},
    order=7,
)

fd_torque = FilterDefinition(
    param_name='min_work_torque',
    model_field='body__max_work_torque',
    filter_type=FilterType.MIN,
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Рабочий момент не менее, Нм',
    label_i18n={'en': 'Working torque min., Nm', 'cn': '最小工作扭矩, Nm'},
    order=7,
    mandatory='yes',
)

fd_body_material = FilterDefinition(
    param_name='body_material_id',
    model_field='body_material',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Материал корпуса',
    label_i18n={'en': 'Body material', 'cn': '壳体材料'},
    order=8,
)

fd_brand = FilterDefinition(
    param_name='brand_id',
    model_field='model_line__brand',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Бренд',
    label_i18n={'en': 'Brand', 'cn': '品牌'},
    order=10,
)

fd_mounting_plate = FilterDefinition(
    param_name='mounting_plate_top_id',
    model_field='body__mounting_plate_top',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Монтажная площадка',
    label_i18n={'en': 'Mounting pad', 'cn': '安装平台'},
    order=11,
)

# ── Legacy flat list (backward compat with old views) ──

GEARBOX_FILTER_DEFINITIONS = [
    fd_ip,
    fd_temp_min,
    fd_temp_max,
    fd_climate,
    fd_torque,
    fd_body_material,
    fd_brand,
    fd_mounting_plate,
]