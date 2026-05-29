# pa_controls/catalog/config.py
"""
Limit-switch-box catalog configuration.
"""
from core.models.catalog_config import CatalogConfig, FilterSet
from pa_controls.models.limit_switch import LimitSwitchBox
from pa_controls.models.lsb_model_line import LimitSwitchModelLine
from pa_controls.catalog.filter_defs import (
    fd_model_line, fd_sensor_variety, fd_points, fd_ip,
    fd_temp_min, fd_temp_max, fd_body_material, fd_brand,
    fd_signal_type, fd_exd,
)


LIMIT_SWITCH_CONFIG = CatalogConfig(
    model_class=LimitSwitchBox,
    model_line_class=LimitSwitchModelLine,

    filter_sets={
        'list': FilterSet(
            definitions=[
                fd_model_line, fd_sensor_variety, fd_points, fd_ip,
                fd_temp_min, fd_temp_max, fd_body_material, fd_brand,
                fd_signal_type, fd_exd,
            ],
            scoped=False,
            show_compatible=True,
        ),
        'model_line': FilterSet(
            definitions=[
                fd_sensor_variety, fd_points, fd_ip,
                fd_temp_min, fd_temp_max, fd_body_material,
                fd_signal_type, fd_exd,
            ],
            scoped=True,
            show_compatible=True,
        ),
        'quickselect': FilterSet(
            definitions=[
                fd_sensor_variety, fd_points, fd_body_material, fd_signal_type,
            ],
            scoped=True,
            show_compatible=False,
        ),
    },

    select_related=[
        'model_line', 'model_line__brand',
        'image_gallery', 'model_line__image_gallery',
        'body', 'sensor_variety', 'primary_sensor',
        'ip', 'body_material', 'body_material_specified', 'sku',
    ],
    prefetch_fields=[
        'image_gallery__items__image',
        'model_line__image_gallery__items__image',
    ],
    search_fields=['code', 'name', 'description'],

    labels={
        'title': 'БКВ',
        'breadcrumbName': 'Блоки концевых выключателей',
        'countLabel': 'БКВ:',
        'searchPlaceholder': 'Поиск БКВ...',
        'emptyLabel': 'БКВ не найдены',
    },
)
