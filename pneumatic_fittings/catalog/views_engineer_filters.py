# pneumatic_fittings/catalog/views_engineer_filters.py
"""
GET /api/pneumatic-fittings/engineer/filters/ — filter options for EngineerSelection.

Опции фильтров считаются в пределах вида каталога (KindFilterOptionsMixin).
"""
from core.access import catalog_permission_classes
from core.views import BaseFilterOptionsView
from pneumatic_fittings.catalog.config import (
    PNEUMATIC_FITTINGS_CONFIG,
    PNEUMATIC_SILENCERS_CONFIG,
    PNEUMATIC_PLUGS_CONFIG,
)
from pneumatic_fittings.catalog.views_common import KindFilterOptionsMixin


class PneumaticFittingsEngineerFilterOptionsView(KindFilterOptionsMixin, BaseFilterOptionsView):
    permission_classes = catalog_permission_classes()

    catalog_config = PNEUMATIC_FITTINGS_CONFIG
    default_scope = 'engineer'


class PneumaticSilencersEngineerFilterOptionsView(KindFilterOptionsMixin, BaseFilterOptionsView):
    permission_classes = catalog_permission_classes()

    catalog_config = PNEUMATIC_SILENCERS_CONFIG
    default_scope = 'engineer'


class PneumaticPlugsEngineerFilterOptionsView(KindFilterOptionsMixin, BaseFilterOptionsView):
    permission_classes = catalog_permission_classes()

    catalog_config = PNEUMATIC_PLUGS_CONFIG
    default_scope = 'engineer'
