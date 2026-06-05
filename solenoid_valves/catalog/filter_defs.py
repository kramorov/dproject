# solenoid_valves/catalog/filter_defs.py
"""
FilterDefinition objects for the solenoid valves (directional valves) catalog.
"""
from core.models.filter_definition import FilterDefinition, FilterType, DataSourceType
from params.models import IpOption, PowerSupplies, PneumaticConnection, ThreadSize
from solenoid_valves.models import ValveFunction, ValveActuationVariety
from materials.models import MaterialGeneral

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

fd_function = FilterDefinition(
    param_name='function_id',
    model_field='function',
    filter_type=FilterType.FUNCTION_COMPATIBLE,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    source_model=ValveFunction,
    label='Схема (функция)',
    order=3,
)

fd_actuation = FilterDefinition(
    param_name='actuation_id',
    model_field='actuation',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    source_model=ValveActuationVariety,
    label='Управление',
    order=4,
)

fd_ip = FilterDefinition(
    param_name='ip_id',
    model_field='ip',
    filter_type=FilterType.IP_RANK,
    data_source_type=DataSourceType.GLOBAL_MODEL,
    source_model=IpOption,
    label='IP',
    order=5,
)

fd_exd = FilterDefinition(
    param_name='exd_id',
    model_field='exd',
    filter_type=FilterType.EXD_COMPATIBLE,
    data_source_type=DataSourceType.CUSTOM,
    label='Взрывозащита',
    order=6,
)

fd_power_supply = FilterDefinition(
    param_name='power_supply_id',
    model_field='power_supply',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    source_model=PowerSupplies,
    label='Напряжение соленоида',
    order=7,
)

fd_kv = FilterDefinition(
    param_name='kv_min',
    model_field='kv',
    filter_type=FilterType.MIN,
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Kv не менее, м³/ч',
    order=8,
)

fd_body_material = FilterDefinition(
    param_name='body_material_id',
    model_field='body_material',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    source_model=MaterialGeneral,
    label='Материал корпуса',
    order=9,
)

fd_solenoid_body_material = FilterDefinition(
    param_name='solenoid_body_material_id',
    model_field='solenoid_body_material',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    source_model=MaterialGeneral,
    label='Материал соленоида',
    order=10,
)

fd_pneumatic_connection = FilterDefinition(
    param_name='pneumatic_connection_id',
    model_field='pneumatic_connection',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    source_model=PneumaticConnection,
    label='Пневматическое присоединение',
    order=11,
)

fd_pneumatic_connection_thread = FilterDefinition(
    param_name='pneumatic_connection_thread_id',
    model_field='pneumatic_connection_thread',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    source_model=ThreadSize,
    label='Резьба присоединения',
    order=12,
)

fd_temp_min = FilterDefinition(
    param_name='work_temp_min',
    model_field='work_temp_min',
    filter_type=FilterType.TEMP_MIN,
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Температура от, °С',
    order=12,
)

fd_temp_max = FilterDefinition(
    param_name='work_temp_max',
    model_field='work_temp_max',
    filter_type=FilterType.TEMP_MAX,
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Температура до, °С',
    order=13,
)

fd_climate = FilterDefinition(
    param_name='climate',
    model_field='work_temp_min',
    filter_type=FilterType.CLIMATE_CASCADE,
    data_source_type=DataSourceType.CUSTOM,
    label='Клим. исполнение',
    order=14,
)

# ── Legacy flat list ──

SOLENOID_VALVES_FILTER_DEFINITIONS = [
    fd_model_line,
    fd_brand,
    fd_function,
    fd_actuation,
    fd_ip,
    fd_exd,
    fd_power_supply,
    fd_kv,
    fd_body_material,
    fd_solenoid_body_material,
    fd_pneumatic_connection,
    fd_pneumatic_connection_thread,
    fd_temp_min,
    fd_temp_max,
    fd_climate,
]