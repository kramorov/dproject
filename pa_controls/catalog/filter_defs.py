# pa_controls/catalog/filter_defs.py
"""
FilterDefinition objects for the limit-switch-box catalog.
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
    param_name='points',
    model_field='points',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.CHOICES,
    choices=[(1, '1 датчик'), (2, '2 датчика'), (3, '3 датчика'), (4, '4 датчика')],
    label='Количество датчиков',
    order=4,
    default_value=2,
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

fd_temp_min = FilterDefinition(
    param_name='work_temp_min',
    model_field='work_temp_min',
    filter_type=FilterType.TEMP_MIN,
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Температура от',
    order=10,
)

fd_temp_max = FilterDefinition(
    param_name='work_temp_max',
    model_field='work_temp_max',
    filter_type=FilterType.TEMP_MAX,
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Температура до',
    order=11,
)

fd_climate = FilterDefinition(
    param_name='climate',
    model_field='work_temp_min',
    filter_type=FilterType.CLIMATE_CASCADE,
    data_source_type=DataSourceType.CUSTOM,
    label='Клим. исполнение',
    order=50,
)

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
    model_field='primary_sensor__signal_type',
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

fd_exd = FilterDefinition(
    param_name='exd_id',
    model_field='exd',
    filter_type=FilterType.EXD_COMPATIBLE,
    data_source_type=DataSourceType.CUSTOM,
    label='Взрывозащита',
    order=51,
)

# ── Legacy flat list ──

LIMIT_SWITCH_FILTER_DEFINITIONS = [
    fd_model_line, fd_sensor_variety, fd_points, fd_ip,
    fd_temp_min, fd_temp_max, fd_body_material, fd_brand,
    fd_climate,
    fd_signal_type, fd_contact_form, fd_exd,
]