# pneumatic_fittings/catalog/config.py
"""
Pneumatic fittings catalog configuration.

Single source of truth: filter sets per page, ORM hints, labels.
"""
from core.models.catalog_config import CatalogConfig, FilterSet
from pneumatic_fittings.models import PneumaticFitting, PneumaticFittingModelLine
from pneumatic_fittings.catalog.filter_defs import (
    fd_model_line, fd_brand, fd_fitting_variety,
    fd_body_material, fd_pipe_material, fd_pipe_diameter,
    fd_thread_type, fd_thread, fd_thread_inner_outer, fd_temp_min,
)


PNEUMATIC_FITTINGS_CONFIG = CatalogConfig(
    model_class=PneumaticFitting,
    model_line_class=PneumaticFittingModelLine,

    filter_sets={
        'list': FilterSet(
            definitions=[
                fd_model_line, fd_brand, fd_fitting_variety,
                fd_body_material, fd_pipe_material, fd_pipe_diameter,
                fd_thread_type, fd_thread, fd_thread_inner_outer,
                fd_temp_min,
            ],
            scoped=False,
            show_compatible=True,
        ),

        'engineer': FilterSet(
            definitions=[
                fd_model_line, fd_brand, fd_fitting_variety,
                fd_body_material, fd_pipe_material, fd_pipe_diameter,
                fd_thread_type, fd_thread, fd_thread_inner_outer,
                fd_temp_min,
            ],
            scoped=False,
            show_compatible=True,
        ),

        'model_line': FilterSet(
            definitions=[
                fd_fitting_variety, fd_body_material, fd_pipe_material,
                fd_pipe_diameter, fd_thread_type, fd_thread,
                fd_thread_inner_outer, fd_temp_min,
            ],
            scoped=True,
            show_compatible=True,
        ),

        'quickselect': FilterSet(
            definitions=[
                fd_fitting_variety, fd_body_material, fd_pipe_material,
                fd_pipe_diameter, fd_thread, fd_thread_inner_outer,
            ],
            scoped=True,
            show_compatible=False,
        ),
    },

    select_related=[
        'model_line',
        'model_line__brand',
        'model_line__fitting_variety',
        'fitting_variety',
        'body_material',
        'pipe_material',
        'thread',
        'thread_inner_outer',
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
    ],
    search_fields=['code', 'name', 'description'],

    labels={
        'title': 'Пневматические фитинги',
        'breadcrumbName': 'Фитинги',
        'countLabel': 'Фитингов:',
        'searchPlaceholder': 'Поиск фитингов...',
        'emptyLabel': 'Фитинги не найдены',
    },
)
