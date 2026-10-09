# pneumatic_fittings/catalog/config.py
"""
Pneumatic fittings catalog configuration.

Single source of truth: filter sets per page, ORM hints, labels.

Три каталога над тремя моделями:
  - PNEUMATIC_FITTINGS_CONFIG   — фитинги резьба-трубка (PneumaticFitting)
  - PNEUMATIC_SILENCERS_CONFIG  — глушители (PneumaticSilencer)
  - PNEUMATIC_PLUGS_CONFIG      — заглушки (PneumaticPlug)

Каждый каталог живёт на своём URL-префиксе
(/api/pneumatic-fittings/, /api/pneumatic-silencers/, /api/pneumatic-plugs/)
и имеет собственный набор фильтров.
"""
from core.models.catalog_config import CatalogConfig, FilterSet
from pneumatic_fittings.models import (
    PneumaticFitting, PneumaticSilencer, PneumaticPlug,
    PneumaticFittingModelLine, PneumaticSilencerModelLine, PneumaticPlugModelLine,
)
from pneumatic_fittings.catalog.filter_defs import (
    fd_model_line, fd_brand, fd_shape, fd_fixation_method,
    fd_body_material, fd_pipe_material, fd_pipe_diameter,
    fd_thread_type, fd_thread, fd_thread_inner_outer, fd_temp_min,
    fd_pressure_min, fd_pressure_max, fd_swivel,
)


# ── Наборы фильтров по видам (композиция fd из filter_defs) ──

# Фитинги резьба-трубка — полный набор
TUBE_DEFINITIONS = [
    fd_model_line, fd_brand, fd_shape, fd_fixation_method,
    fd_body_material, fd_pipe_material, fd_pipe_diameter,
    fd_thread_type, fd_thread, fd_thread_inner_outer,
    fd_temp_min, fd_pressure_min, fd_pressure_max, fd_swivel,
]
TUBE_MODEL_LINE_DEFINITIONS = [
    fd_shape, fd_fixation_method, fd_body_material, fd_pipe_material,
    fd_pipe_diameter, fd_thread_type, fd_thread,
    fd_thread_inner_outer, fd_temp_min, fd_pressure_min, fd_pressure_max,
]
TUBE_QUICKSELECT_DEFINITIONS = [
    fd_shape, fd_fixation_method, fd_body_material, fd_pipe_material,
    fd_pipe_diameter, fd_thread, fd_thread_inner_outer,
]

# Глушители и заглушки — без трубки/разновидности/поворотности
SILENCER_DEFINITIONS = [
    fd_model_line, fd_brand, fd_body_material,
    fd_thread_type, fd_thread, fd_thread_inner_outer,
    fd_temp_min, fd_pressure_min, fd_pressure_max,
]
SILENCER_MODEL_LINE_DEFINITIONS = [
    fd_body_material, fd_thread_type, fd_thread,
    fd_thread_inner_outer, fd_temp_min, fd_pressure_min, fd_pressure_max,
]
SILENCER_QUICKSELECT_DEFINITIONS = [
    fd_body_material, fd_thread, fd_thread_inner_outer,
]
PLUG_DEFINITIONS = list(SILENCER_DEFINITIONS)
PLUG_MODEL_LINE_DEFINITIONS = list(SILENCER_MODEL_LINE_DEFINITIONS)
PLUG_QUICKSELECT_DEFINITIONS = list(SILENCER_QUICKSELECT_DEFINITIONS)


# ── Общие ORM-подсказки ──

_PREFETCH_COMMON = [
    'image_gallery__items__image__variants',
    'image_gallery__items__image',
    'tech_docs',
    'model_line__image_gallery__items__image__variants',
    'model_line__image_gallery__items__image',
    'model_line__tech_docs',
]

_SELECT_RELATED_COMMON = [
    'model_line',
    'model_line__brand', 'model_line__equipment_type',
    'body_material',
    'thread',
    'thread_inner_outer',
    'sku',
]

_TUBE_SELECT_RELATED = _SELECT_RELATED_COMMON + [
    'model_line__shape', 'model_line__fixation_method', 'pipe_material',
]


PNEUMATIC_FITTINGS_CONFIG = CatalogConfig(
    model_class=PneumaticFitting,
    model_line_class=PneumaticFittingModelLine,

    filter_sets={
        'list': FilterSet(
            definitions=TUBE_DEFINITIONS,
            scoped=False,
            show_compatible=True,
        ),

        'engineer': FilterSet(
            definitions=TUBE_DEFINITIONS,
            scoped=False,
            show_compatible=True,
        ),

        'model_line': FilterSet(
            definitions=TUBE_MODEL_LINE_DEFINITIONS,
            scoped=True,
            show_compatible=True,
        ),

        'quickselect': FilterSet(
            definitions=TUBE_QUICKSELECT_DEFINITIONS,
            scoped=True,
            show_compatible=False,
        ),
    },

    select_related=_TUBE_SELECT_RELATED,
    prefetch_fields=_PREFETCH_COMMON,
    search_fields=['code', 'name', 'description'],

    labels={
        'title': 'Пневматические фитинги',
        'breadcrumbName': 'Фитинги',
        'countLabel': 'Фитингов:',
        'searchPlaceholder': 'Поиск фитингов...',
        'emptyLabel': 'Фитинги не найдены',
    },
)


PNEUMATIC_SILENCERS_CONFIG = CatalogConfig(
    model_class=PneumaticSilencer,
    model_line_class=PneumaticSilencerModelLine,

    filter_sets={
        'list': FilterSet(
            definitions=SILENCER_DEFINITIONS,
            scoped=False,
            show_compatible=True,
        ),
        'engineer': FilterSet(
            definitions=SILENCER_DEFINITIONS,
            scoped=False,
            show_compatible=True,
        ),
        'model_line': FilterSet(
            definitions=SILENCER_MODEL_LINE_DEFINITIONS,
            scoped=True,
            show_compatible=True,
        ),
        'quickselect': FilterSet(
            definitions=SILENCER_QUICKSELECT_DEFINITIONS,
            scoped=True,
            show_compatible=False,
        ),
    },

    select_related=_SELECT_RELATED_COMMON,
    prefetch_fields=_PREFETCH_COMMON,
    search_fields=['code', 'name', 'description'],

    labels={
        'title': 'Глушители пневматические',
        'breadcrumbName': 'Глушители',
        'countLabel': 'Глушителей:',
        'searchPlaceholder': 'Поиск глушителей...',
        'emptyLabel': 'Глушители не найдены',
    },
)


PNEUMATIC_PLUGS_CONFIG = CatalogConfig(
    model_class=PneumaticPlug,
    model_line_class=PneumaticPlugModelLine,

    filter_sets={
        'list': FilterSet(
            definitions=PLUG_DEFINITIONS,
            scoped=False,
            show_compatible=True,
        ),
        'engineer': FilterSet(
            definitions=PLUG_DEFINITIONS,
            scoped=False,
            show_compatible=True,
        ),
        'model_line': FilterSet(
            definitions=PLUG_MODEL_LINE_DEFINITIONS,
            scoped=True,
            show_compatible=True,
        ),
        'quickselect': FilterSet(
            definitions=PLUG_QUICKSELECT_DEFINITIONS,
            scoped=True,
            show_compatible=False,
        ),
    },

    select_related=_SELECT_RELATED_COMMON,
    prefetch_fields=_PREFETCH_COMMON,
    search_fields=['code', 'name', 'description'],

    labels={
        'title': 'Заглушки пневматические',
        'breadcrumbName': 'Заглушки',
        'countLabel': 'Заглушек:',
        'searchPlaceholder': 'Поиск заглушек...',
        'emptyLabel': 'Заглушки не найдены',
    },
)
