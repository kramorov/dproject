# solenoid_valves/catalog/config.py
"""
Solenoid valves (directional valves) catalog configuration.

Single source of truth: filter sets per page, ORM hints, labels.
"""
from core.models.catalog_config import CatalogConfig, FilterSet
from solenoid_valves.models import DirectionValve
from solenoid_valves.models.dv_model_line import DirectionalValveModelLine
from solenoid_valves.catalog.filter_defs import (
    fd_model_line, fd_brand, fd_function, fd_actuation,
    fd_ip, fd_exd, fd_power_supply, fd_kv,
    fd_body_material, fd_solenoid_body_material, fd_pneumatic_connection,
    fd_temp_min, fd_temp_max, fd_climate,
)


SOLENOID_VALVES_CONFIG = CatalogConfig(
    model_class=DirectionValve,
    model_line_class=DirectionalValveModelLine,

    filter_sets={
        # ── Engineering Selection: max filters, global values ──
        'list': FilterSet(
            definitions=[
                fd_model_line, fd_brand, fd_function, fd_actuation,
                fd_ip, fd_exd, fd_power_supply, fd_kv,
                fd_body_material, fd_solenoid_body_material,
                fd_pneumatic_connection, fd_climate,
            ],
            scoped=False,
            show_compatible=True,
        ),

        'engineer': FilterSet(
            definitions=[
                fd_model_line, fd_brand, fd_function, fd_actuation,
                fd_ip, fd_exd, fd_power_supply, fd_kv,
                fd_body_material, fd_solenoid_body_material,
                fd_pneumatic_connection, fd_climate,
            ],
            scoped=False,
            show_compatible=True,
        ),

        # ── Series page: no brand, values scoped to model_line ──
        'model_line': FilterSet(
            definitions=[
                fd_function, fd_actuation,
                fd_ip, fd_exd, fd_power_supply, fd_kv,
                fd_body_material, fd_solenoid_body_material,
                fd_pneumatic_connection,
                fd_temp_min, fd_temp_max, fd_climate,
            ],
            scoped=True,
            show_compatible=True,
        ),

        # ── Quick Select: chip filters only ──
        'quickselect': FilterSet(
            definitions=[
                fd_function, fd_actuation,
                fd_body_material, fd_kv,
            ],
            scoped=True,
            show_compatible=False,
        ),
    },

    select_related=[
        'model_line',
        'model_line__brand',
        'model_line__construction',
        'model_line__operation',
        'model_line__working_medium',
        'body',
        'function',
        'actuation',
        'manual_override',
        'power_supply',
        'ip',
        'exd',
        'body_material',
        'body_material_specified',
        'sealing_material_specified',
        'solenoid_body_material',
        'solenoid_body_material_specified',
        'pneumatic_connection',
        'pneumatic_connection_thread',
        'cable_glands_holes',
        'brand',
        'producer',
        'sku',
    ],
    prefetch_fields=[
        'image_gallery__items__image__variants',
        'image_gallery__items__image',
        'tech_docs',
        'model_line__image_gallery__items__image__variants',
        'model_line__image_gallery__items__image',
        'model_line__tech_docs',
        'model_line__cert_docs',
    ],
    search_fields=['code', 'name', 'description'],

    labels={
        'title': 'Распределительные клапаны',
        'breadcrumbName': 'Клапаны',
        'countLabel': 'Клапанов:',
        'searchPlaceholder': 'Поиск клапанов...',
        'emptyLabel': 'Клапаны не найдены',
    },
)
