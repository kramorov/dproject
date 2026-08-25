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
    fd_signal_type, fd_contact_form, fd_exd, fd_climate,
    fd_visual_indicator,
)


LIMIT_SWITCH_CONFIG = CatalogConfig(
    model_class=LimitSwitchBox,
    model_line_class=LimitSwitchModelLine,

    filter_sets={
        'list': FilterSet(
            definitions=[
                fd_model_line, fd_sensor_variety, fd_points, fd_ip,
                fd_temp_min, fd_temp_max, fd_body_material, fd_brand,
                fd_signal_type, fd_contact_form, fd_visual_indicator,
                fd_exd, fd_climate,
            ],
            scoped=False,
            show_compatible=True,
        ),
        'engineer': FilterSet(
            definitions=[
                fd_model_line, fd_sensor_variety, fd_points, fd_ip,
                fd_temp_min, fd_temp_max, fd_body_material, fd_brand,
                fd_signal_type, fd_contact_form, fd_visual_indicator,
                fd_exd, fd_climate,
            ],
            scoped=False,
            show_compatible=True,
        ),

        'model_line': FilterSet(
            definitions=[
                fd_sensor_variety, fd_points, fd_ip,
                fd_temp_min, fd_temp_max, fd_body_material,
                fd_signal_type, fd_visual_indicator,
                fd_exd, fd_climate,
            ],
            scoped=True,
            show_compatible=True,
        ),
        'quickselect': FilterSet(
            definitions=[
                fd_sensor_variety, fd_points, fd_body_material, fd_signal_type,
                fd_visual_indicator, fd_exd, fd_temp_min, fd_temp_max,
            ],
            scoped=True,
            show_compatible=False,
            defaults={
                'sensor_variety_id': 'first',
                'points_option_id': 'first',
                'body_material_id': 'first',
                'signal_type_id': 'first',
                'exd_id': 'first',
                'work_temp_min': 'first',
                'work_temp_max': 'first',
            },
        ),
    },

    select_related=[
        'model_line', 'model_line__brand', 'model_line__equipment_type',
        'image_gallery', 'model_line__image_gallery',
        'body', 'sensor_variety', 'primary_sensor', 'signal_profile',
        'visual_indicator_type',
        'ip', 'body_material', 'body_material_specified', 'sku',
    ],
    prefetch_fields=[
        'image_gallery__items__image__variants',
        'image_gallery__items__image',
        'model_line__image_gallery__items__image__variants',
        'model_line__image_gallery__items__image',
        'signal_profile__entries__signal_role',
        'signal_profile__entries__sensor__signal_type',
        'signal_profile__entries__input_signal',
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