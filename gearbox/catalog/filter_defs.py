# gearbox/catalog/filter_defs.py
"""
FilterDefinition objects for the gearbox catalog.

These are the same FilterDefinitions previously in gearbox/services/filters.py.
Kept here for the CatalogConfig; the old location remains for backward compat.
"""
from core.models.filter_definition import FilterDefinition, FilterType, DataSourceType
from params.models import IpOption, ClimaticPlacementCategory, ClimaticZoneCategory
from params.models import IpOption

# ── Individual filter definitions (named for reuse in FilterSets) ──

fd_ip = FilterDefinition(
    param_name='ip_id',
    model_field='ip',
    filter_type=FilterType.IP_RANK,
    data_source_type=DataSourceType.GLOBAL_MODEL,
    source_model=IpOption,
    label='IP',
    order=4,
)

fd_temp_min = FilterDefinition(
    param_name='work_temp_min',
    model_field='work_temp_min',
    filter_type=FilterType.TEMP_MIN,
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Температура от, °С',
    order=5,
)

fd_temp_max = FilterDefinition(
    param_name='work_temp_max',
    model_field='work_temp_max',
    filter_type=FilterType.TEMP_MAX,
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Температура до, °С',
    order=6,
)

fd_climate = FilterDefinition(
    param_name='climate',
    model_field='work_temp_min',
    filter_type=FilterType.CLIMATE_CASCADE,
    data_source_type=DataSourceType.CUSTOM,
    label='Клим. исполнение',
    order=7,
)

fd_torque = FilterDefinition(
    param_name='min_work_torque',
    model_field='body__max_work_torque',
    filter_type=FilterType.MIN,
    data_source_type=DataSourceType.FIELD_VALUES,
    label='Рабочий момент не менее, Нм',
    order=7,
    mandatory='yes',
)

fd_body_material = FilterDefinition(
    param_name='body_material_id',
    model_field='body_material',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Материал корпуса',
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

fd_mounting_plate = FilterDefinition(
    param_name='mounting_plate_top_id',
    model_field='body__mounting_plate_top',
    filter_type=FilterType.EXACT,
    data_source_type=DataSourceType.UNIQUE_FIELD_VALUES,
    label='Монтажная площадка',
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