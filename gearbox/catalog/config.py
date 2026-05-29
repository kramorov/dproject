# gearbox/catalog/config.py
"""
Gearbox catalog configuration.

Single source of truth: filter sets per page, ORM hints, labels.
Import GEARBOX_CONFIG from here and pass to BaseFilterOptionsView / views.
"""
from core.models.catalog_config import CatalogConfig, FilterSet
from gearbox.models import GearBox
from gearbox.models.gb_model_line import GearBoxModelLine
from gearbox.catalog.filter_defs import (
    fd_ip, fd_temp_min, fd_temp_max, fd_torque,
    fd_body_material, fd_brand, fd_mounting_plate,
)


GEARBOX_CONFIG = CatalogConfig(
    model_class=GearBox,
    model_line_class=GearBoxModelLine,

    filter_sets={
        # ── Engineering Selection: max filters, global values ──
        'list': FilterSet(
            definitions=[
                fd_ip,
                fd_temp_min,
                fd_temp_max,
                fd_torque,
                fd_body_material,
                fd_brand,
                fd_mounting_plate,
            ],
            scoped=False,
            show_compatible=True,
        ),

        # ── Series page: no brand, values scoped to model_line ──
        'model_line': FilterSet(
            definitions=[
                fd_ip,
                fd_temp_min,
                fd_temp_max,
                fd_torque,
                fd_body_material,
                fd_mounting_plate,
            ],
            scoped=True,
            show_compatible=True,
        ),

        # ── Quick Select: chip filters only, no exact/compatible split ──
        'quickselect': FilterSet(
            definitions=[
                fd_body_material,
                fd_torque,
                fd_mounting_plate,
            ],
            scoped=True,
            show_compatible=False,
        ),
    },

    select_related=[
        'model_line',
        'model_line__brand',
        'model_line__gearbox_output_variety',
        'model_line__gearbox_variety',
        'body',
        'body__transmission_variety',
        'ip',
        'body_material',
        'sku',
    ],
    prefetch_fields=[
        'image_gallery__items__image',
        'tech_docs',
        'model_line__image_gallery__items__image',
        'model_line__tech_docs',
        'model_line__cert_docs',
        'body__mounting_plate_top',
        'body__mounting_plate_bottom',
    ],
    search_fields=['code', 'name', 'description'],

    labels={
        'title': 'Редукторы',
        'breadcrumbName': 'Редукторы',
        'countLabel': 'Редукторов:',
        'searchPlaceholder': 'Поиск редукторов...',
        'emptyLabel': 'Редукторы не найдены',
    },
)
