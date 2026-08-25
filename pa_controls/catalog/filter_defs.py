# pa_controls/catalog/filter_defs.py
"""
FilterDefinition objects for the limit-switch-box catalog.

Temperature, Exd, IP filters now delegate to ParameterRule (configurator)
via parameter_rule_code, while keeping original filter_type for frontend
compatibility (specialized UI components: temp slider, Exd cascade, IP rank).
"""
from core.models.filter_definition import FilterDefinition, FilterType, DataSourceType
from params.models import IpOption

fd_model_line = FilterDefinition(
    param_name='model_line_id',
    model_field='model_line',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.FOREIGN_KEY,
    label='Серия',
    order=7,
)

fd_sensor_variety = FilterDefinition(
    param_name='sensor_variety_id',
    model_field='sensor_variety',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Тип сенсора',
    order=1,
)

fd_points = FilterDefinition(
    param_name='points_option_id',
    model_field='points_option',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.FOREIGN_KEY,
    label='Количество датчиков',
    order=4,
    default_value=2,
)

# ── ParameterRule-backed filters: filter_type for frontend, parameter_rule_code for backend ──

fd_ip = FilterDefinition(
    param_name='ip_id',
    model_field='ip',
    filter_type=FilterType.IP_RANK,            # frontend: IP rank UI
    parameter_rule_code='ip',                  # backend: ParameterRule 'ip'
    data_source_type=DataSourceType.GLOBAL_MODEL,
    source_model=IpOption,
    label='IP',
    order=5,
)

fd_temp_min = FilterDefinition(
    param_name='work_temp_min',
    model_field='work_temp_min',
    filter_type=FilterType.TEMP_MIN,            # frontend: temperature slider
    parameter_rule_code='temperature_min',      # backend: ParameterRule
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Температура от',
    order=10,
)

fd_temp_max = FilterDefinition(
    param_name='work_temp_max',
    model_field='work_temp_max',
    filter_type=FilterType.TEMP_MAX,            # frontend: temperature slider
    parameter_rule_code='temperature_max',      # backend: ParameterRule
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Температура до',
    order=11,
)

fd_exd = FilterDefinition(
    param_name='exd_id',
    model_field='exd',
    filter_type=FilterType.EXD_COMPATIBLE,      # frontend: Exd cascade UI
    parameter_rule_code='exd',                  # backend: ParameterRule
    data_source_type=DataSourceType.CUSTOM,
    label='Взрывозащита',
    order=51,
)

fd_climate = FilterDefinition(
    param_name='climate',
    model_field='work_temp_min',
    filter_type=FilterType.CLIMATE_CASCADE,     # frontend: ClimateFilter slider
    data_source_type=DataSourceType.CUSTOM,
    label='Клим. исполнение',
    order=50,
)

# ── OLD definitions without parameter_rule_code (commented out for rollback) ──
#
# fd_ip = FilterDefinition(
#     param_name='ip_id',
#     model_field='ip',
#     filter_type=FilterType.IP_RANK,
#     data_source_type=DataSourceType.GLOBAL_MODEL,
#     source_model=IpOption,
#     label='IP',
#     order=5,
# )
#
# fd_temp_min = FilterDefinition(
#     param_name='work_temp_min',
#     model_field='work_temp_min',
#     filter_type=FilterType.TEMP_MIN,
#     data_source_type=DataSourceType.FIELD_VALUES,
#     label='Температура от',
#     order=10,
# )
#
# fd_temp_max = FilterDefinition(
#     param_name='work_temp_max',
#     model_field='work_temp_max',
#     filter_type=FilterType.TEMP_MAX,
#     data_source_type=DataSourceType.FIELD_VALUES,
#     label='Температура до',
#     order=11,
# )
#
# fd_exd = FilterDefinition(
#     param_name='exd_id',
#     model_field='exd',
#     filter_type=FilterType.EXD_COMPATIBLE,
#     data_source_type=DataSourceType.CUSTOM,
#     label='Взрывозащита',
#     order=51,
# )

fd_body_material = FilterDefinition(
    param_name='body_material_id',
    model_field='body_material',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.FOREIGN_KEY,
    label='Материал корпуса',
    order=6,
)

fd_brand = FilterDefinition(
    param_name='model_line_brand_id',
    model_field='model_line__brand',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Бренд серии',
    order=8,
)

fd_signal_type = FilterDefinition(
    param_name='signal_type_id',
    model_field='signal_profile__entries__sensor__signal_type',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Тип сигнала',
    order=2,
)

fd_contact_form = FilterDefinition(
    param_name='contact_form_id',
    model_field='primary_sensor__contact_form',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Форма контактов',
    order=3,
    show_code=True,
)

fd_visual_indicator = FilterDefinition(
    param_name='visual_indicator_type_id',
    model_field='visual_indicator_type',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Вид визуального индикатора',
    order=4,
)

LIMIT_SWITCH_FILTER_DEFINITIONS = [
    fd_model_line, fd_sensor_variety, fd_points,
    fd_ip, fd_temp_min, fd_temp_max,
    fd_body_material, fd_brand,
    fd_signal_type, fd_contact_form, fd_visual_indicator,
    fd_exd,
]
