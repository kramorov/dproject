# pa_controls/catalog/posi_filter_defs.py
"""
FilterDefinition objects for the positioners catalog (PosiModelLineItem).

По образцу БКВ (filter_defs.py): температура/Exd/IP делегируют в ParameterRule
(configurator) через parameter_rule_code, filter_type остаётся для фронта
(специальные UI-компоненты: temp-слайдер, Exd-каскад, IP-ранг).
"""
from core.models.filter_definition import FilterDefinition, FilterType, DataSourceType
from params.models import IpOption
from pa_controls.models.posi_options import ActingType, LeverOption, SmartCapabilitySet
from pa_controls.models.posi_body_connections import PosiBodyConnections

fd_model_line = FilterDefinition(
    param_name='model_line_id',
    model_field='model_line',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.FOREIGN_KEY,
    label='Серия',
    label_i18n={'en': 'Series', 'cn': '系列'},
    order=1,
)

fd_brand = FilterDefinition(
    param_name='brand_id',
    model_field='model_line__brand',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Бренд серии',
    label_i18n={'en': 'Series brand', 'cn': '系列品牌'},
    order=2,
)

fd_acting_type = FilterDefinition(
    param_name='acting_type_id',
    model_field='acting_type',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.FOREIGN_KEY,
    source_model=ActingType,
    label='Тип действия',
    label_i18n={'en': 'Acting type', 'cn': '动作类型'},
    order=3,
)

fd_body_connection = FilterDefinition(
    param_name='body_connection_id',
    model_field='body_connection',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.FOREIGN_KEY,
    source_model=PosiBodyConnections,
    label='Присоединения корпуса',
    label_i18n={'en': 'Body connections', 'cn': '阀体连接'},
    order=4,
)

fd_lever = FilterDefinition(
    param_name='lever_id',
    model_field='lever',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.FOREIGN_KEY,
    source_model=LeverOption,
    label='Рычаг',
    label_i18n={'en': 'Lever', 'cn': '杠杆'},
    order=5,
)

fd_signal_profile = FilterDefinition(
    param_name='signal_profile_id',
    model_field='signal_profile',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Профиль сигналов',
    label_i18n={'en': 'Signal profile', 'cn': '信号配置'},
    order=6,
)

fd_alarm = FilterDefinition(
    param_name='alarm_id',
    model_field='alarm',
    filter_type=FilterType.EXACT,
    # UNIQUE_FIELD_VALUES: только профили, реально используемые как тревога
    # в карточках (входные профили 4-20/HART сюда не попадают).
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Сигнал тревоги',
    label_i18n={'en': 'Alarm', 'cn': '报警'},
    order=7,
)

fd_smart = FilterDefinition(
    param_name='smart_capability_set_id',
    model_field='smart_capability_set',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.FOREIGN_KEY,
    source_model=SmartCapabilitySet,
    label='Смарт-возможности',
    label_i18n={'en': 'Smart capabilities', 'cn': '智能功能'},
    order=8,
)

fd_body_material = FilterDefinition(
    param_name='body_material_id',
    model_field='model_line__body_material',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Материал корпуса',
    label_i18n={'en': 'Body material', 'cn': '壳体材料'},
    order=9,
)

# ── ParameterRule-backed filters: filter_type для фронта, parameter_rule_code для бэка ──

fd_ip = FilterDefinition(
    param_name='ip_id',
    model_field='model_line__ip',
    filter_type=FilterType.IP_RANK,            # frontend: IP rank UI
    parameter_rule_code='ip',                  # backend: ParameterRule 'ip'
    data_source_type=DataSourceType.GLOBAL_MODEL,
    source_model=IpOption,
    label='IP',
    label_i18n={'en': 'IP', 'cn': 'IP'},
    order=10,
)

fd_temp_min = FilterDefinition(
    param_name='work_temp_min',
    model_field='work_temp_min',
    filter_type=FilterType.TEMP_MIN,
    parameter_rule_code='temperature_min',
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Температура от',
    label_i18n={'en': 'Temperature from', 'cn': '温度从'},
    order=11,
)

fd_temp_max = FilterDefinition(
    param_name='work_temp_max',
    model_field='work_temp_max',
    filter_type=FilterType.TEMP_MAX,
    parameter_rule_code='temperature_max',
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Температура до',
    label_i18n={'en': 'Temperature to', 'cn': '温度至'},
    order=12,
)

fd_exd = FilterDefinition(
    param_name='exd_id',
    model_field='exd_options',
    filter_type=FilterType.EXD_COMPATIBLE,      # frontend: Exd cascade UI
    parameter_rule_code='exd',                  # backend: ParameterRule 'exd'
    data_source_type=DataSourceType.CUSTOM,
    label='Взрывозащита',
    label_i18n={'en': 'Explosion protection', 'cn': '防爆'},
    order=13,
)

POSI_FILTER_DEFINITIONS = [
    fd_model_line, fd_brand, fd_acting_type,
    fd_body_connection, fd_lever, fd_signal_profile, fd_alarm, fd_smart,
    fd_body_material, fd_ip, fd_temp_min, fd_temp_max, fd_exd,
]

# Фильтры быстрого подбора (QuickSelect) — список param_name.
POSI_QUICKSELECT_FILTERS = [
    'body_connection_id',
    'lever_id',
    'signal_profile_id',
    'exd_id',
    'work_temp_min',
    'work_temp_max',
]
