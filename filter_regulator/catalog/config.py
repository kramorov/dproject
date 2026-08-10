# filter_regulator/catalog/config.py
"""
Filter-regulator catalog configuration.
"""
from core.models.catalog_config import CatalogConfig, FilterSet
from filter_regulator.models import FilterRegulator
from filter_regulator.models.fr_model_line import FilterRegulatorModelLine
from filter_regulator.catalog.filter_defs import (
    fd_model_line, fd_filtration, fd_body_material, fd_flow_rate,
    fd_thread, fd_thread_type, fd_temp_min, fd_temp_max, fd_brand,
    fd_climate,
)


FILTER_REGULATOR_CONFIG = CatalogConfig(
    model_class=FilterRegulator,
    model_line_class=FilterRegulatorModelLine,

    filter_sets={
        'list': FilterSet(
            definitions=[
                fd_model_line, fd_filtration, fd_body_material,
                fd_flow_rate, fd_thread, fd_temp_min, fd_temp_max, fd_climate, fd_brand,
            ],
            scoped=False,
            show_compatible=False,
        ),
        'engineer': FilterSet(
            definitions=[
                fd_model_line, fd_filtration, fd_body_material,
                fd_flow_rate, fd_thread, fd_temp_min, fd_temp_max, fd_climate, fd_brand,
            ],
            scoped=False,
            show_compatible=False,
        ),

        'model_line': FilterSet(
            definitions=[
                fd_filtration, fd_body_material,
                fd_flow_rate, fd_thread,
                fd_temp_min, fd_temp_max, fd_climate,
            ],
            scoped=True,
            show_compatible=False,
        ),
        'quickselect': FilterSet(
            definitions=[
                fd_filtration, fd_body_material, fd_flow_rate, fd_thread,
            ],
            scoped=True,
            show_compatible=False,
            defaults={
                'filtration_rating_min': 'first',
                'body_material_id': 'first',
                'flow_rate_min': 'first',
                'thread_id': 'first',
            },
        ),
    },

    select_related=[
        'model_line', 'model_line__brand', 'model_line__equipment_type', 'model_line__filter_variety',
        'body', 'body__thread', 'body__gauge_port_size',
        'body__drain_port_size', 'ip', 'body_material',
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
        'title': 'Фильтр-регуляторы',
        'breadcrumbName': 'Фильтр-регуляторы',
        'countLabel': 'Фильтр-регуляторов:',
        'searchPlaceholder': 'Поиск фильтр-регуляторов...',
        'emptyLabel': 'Фильтр-регуляторы не найдены',
    },
)