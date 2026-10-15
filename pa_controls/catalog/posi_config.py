# pa_controls/catalog/posi_config.py
"""
Positioners catalog configuration (PosiModelLineItem).
"""
from core.models.catalog_config import CatalogConfig, FilterSet
from pa_controls.models.positioner_item import PosiModelLineItem
from pa_controls.models.posi_model_line import PosiModelLine
from pa_controls.catalog.posi_filter_defs import (
    fd_model_line, fd_brand, fd_acting_type,
    fd_body_connection, fd_lever, fd_signal_profile, fd_alarm, fd_smart,
    fd_body_material, fd_ip, fd_temp_min, fd_temp_max, fd_exd,
)


POSI_CONFIG = CatalogConfig(
    model_class=PosiModelLineItem,
    model_line_class=PosiModelLine,

    filter_sets={
        'list': FilterSet(
            definitions=[
                fd_model_line, fd_brand, fd_acting_type,
                fd_body_connection, fd_lever, fd_signal_profile, fd_alarm, fd_smart,
                fd_body_material, fd_ip, fd_temp_min, fd_temp_max, fd_exd,
            ],
            scoped=False,
            show_compatible=True,
        ),
        'engineer': FilterSet(
            definitions=[
                fd_model_line, fd_brand, fd_acting_type,
                fd_body_connection, fd_lever, fd_signal_profile, fd_alarm, fd_smart,
                fd_body_material, fd_ip, fd_temp_min, fd_temp_max, fd_exd,
            ],
            scoped=False,
            show_compatible=True,
        ),
        'model_line': FilterSet(
            definitions=[
                fd_acting_type,
                fd_body_connection, fd_lever, fd_signal_profile, fd_alarm, fd_smart,
                fd_body_material, fd_ip, fd_temp_min, fd_temp_max, fd_exd,
            ],
            scoped=True,
            show_compatible=True,
        ),
        'quickselect': FilterSet(
            definitions=[
                fd_body_connection, fd_lever, fd_signal_profile,
                fd_exd, fd_temp_min, fd_temp_max,
            ],
            scoped=True,
            show_compatible=False,
            defaults={
                'body_connection_id': 'first',
                'lever_id': 'first',
                'signal_profile_id': 'first',
                'exd_id': 'first',
                'work_temp_min': 'first',
                'work_temp_max': 'first',
            },
        ),
    },

    select_related=[
        'model_line', 'model_line__brand', 'model_line__equipment_type',
        'model_line__ip', 'model_line__body_material',
        'acting_type', 'body_connection',
        'body_connection__pneumatic_thread', 'body_connection__cable_gland_hole',
        'lever', 'signal_profile', 'alarm', 'smart_capability_set',
        'image_gallery', 'model_line__image_gallery',
        'sku',
    ],
    prefetch_fields=[
        'image_gallery__items__image__variants',
        'image_gallery__items__image',
        'model_line__image_gallery__items__image__variants',
        'model_line__image_gallery__items__image',
        'exd_options',
        'signal_profile__entries__signal_role',
        'signal_profile__entries__sensor__signal_type',
        'signal_profile__entries__input_signal',
    ],
    search_fields=['code', 'name', 'description'],

    labels={
        'title': 'Позиционеры',
        'breadcrumbName': 'Позиционеры',
        'countLabel': 'Позиционеров:',
        'searchPlaceholder': 'Поиск позиционеров...',
        'emptyLabel': 'Позиционеры не найдены',
    },
)
