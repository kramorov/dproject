# cable_glands/catalog/config.py
"""
Cable glands catalog configuration.

Единый источник правды: наборы фильтров по страницам, подсказки ORM, подписи.
Паттерн — solenoid_valves/catalog/config.py.
"""
from core.models.catalog_config import CatalogConfig, FilterSet
from cable_glands.models import CableGland
from cable_glands.models.cg_model_line import CableGlandModelLine
from cable_glands.catalog.filter_defs import (
    fd_model_line, fd_brand, fd_thread, fd_body_material,
    fd_exd, fd_ip,
    fd_cable_diameter_min, fd_cable_diameter_max,
    fd_cable_diameter_outer_min, fd_cable_diameter_outer_max,
    fd_temp_min, fd_temp_max, fd_climate,
    fd_cable_type,
)


CABLE_GLAND_CONFIG = CatalogConfig(
    model_class=CableGland,
    model_line_class=CableGlandModelLine,

    filter_sets={
        # ── Каталог: максимум фильтров, глобальные значения ──
        'list': FilterSet(
            definitions=[
                fd_model_line, fd_brand, fd_thread, fd_body_material,
                fd_exd, fd_ip,
                fd_cable_diameter_min, fd_cable_diameter_max,
                fd_cable_diameter_outer_min, fd_cable_diameter_outer_max,
                fd_temp_min, fd_temp_max, fd_climate,
                fd_cable_type,
            ],
            scoped=False,
            show_compatible=True,
        ),

        'engineer': FilterSet(
            definitions=[
                fd_model_line, fd_brand, fd_thread, fd_body_material,
                fd_exd, fd_ip,
                fd_cable_diameter_min, fd_cable_diameter_max,
                fd_cable_diameter_outer_min, fd_cable_diameter_outer_max,
                fd_temp_min, fd_temp_max, fd_climate,
                fd_cable_type,
            ],
            scoped=False,
            show_compatible=True,
        ),

        # ── Страница серии: без бренда, значения ограничены серией ──
        'model_line': FilterSet(
            definitions=[
                fd_thread, fd_body_material, fd_exd, fd_ip,
                fd_cable_diameter_min, fd_cable_diameter_max,
                fd_cable_diameter_outer_min, fd_cable_diameter_outer_max,
                fd_temp_min, fd_temp_max, fd_climate,
            ],
            scoped=True,
            show_compatible=True,
        ),

        # ── Быстрый подбор: только чипсы ──
        'quickselect': FilterSet(
            definitions=[
                fd_thread, fd_body_material, fd_exd, fd_ip,
                fd_cable_type,
                fd_cable_diameter_min, fd_cable_diameter_max,
                fd_temp_min,
            ],
            scoped=True,
            show_compatible=False,
            defaults={
                'thread_id': 'first',
                'body_material_id': 'first',
                'ip_id': 'first',
                'exd_id': 'first',
            },
        ),
    },

    select_related=[
        'model_line',
        'model_line__brand', 'model_line__equipment_type', 'model_line__cable_type',
        'model_line_item',
        'model_line_item__body',
        'model_line_item__metal_sleeve_body',
        'thread_option', 'thread_option__thread_size',
        'body_material_option', 'body_material_option__body_material',
        'exd_option',
        'sku',
    ],
    prefetch_fields=[
        'model_line__ip',
        'exd_option__exd_options',
        'exd_option__exd_options__explosion_protection_class',
        'exd_option__exd_options__hazardous_group',
        'model_line_item__metal_sleeve_body__metal_sleeve',
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
        'title': 'Кабельные вводы',
        'breadcrumbName': 'Кабельные вводы',
        'countLabel': 'Вводов:',
        'searchPlaceholder': 'Поиск кабельных вводов...',
        'emptyLabel': 'Кабельные вводы не найдены',
    },
)
