# pneumatic_fittings/catalog/views_filters.py
"""
GET /api/pneumatic-fittings/filters/ — filter options for FilterSidebar.

Опции фильтров считаются в пределах вида каталога (KindFilterOptionsMixin).
"""
from rest_framework.permissions import AllowAny
from core.views import BaseFilterOptionsView
from pneumatic_fittings.catalog.config import (
    PNEUMATIC_FITTINGS_CONFIG,
    PNEUMATIC_SILENCERS_CONFIG,
    PNEUMATIC_PLUGS_CONFIG,
)
from pneumatic_fittings.catalog.views_common import KindFilterOptionsMixin


class PneumaticFittingsFilterOptionsView(KindFilterOptionsMixin, BaseFilterOptionsView):
    permission_classes = [AllowAny]
    catalog_config = PNEUMATIC_FITTINGS_CONFIG


class PneumaticSilencersFilterOptionsView(KindFilterOptionsMixin, BaseFilterOptionsView):
    permission_classes = [AllowAny]
    catalog_config = PNEUMATIC_SILENCERS_CONFIG


class PneumaticPlugsFilterOptionsView(KindFilterOptionsMixin, BaseFilterOptionsView):
    permission_classes = [AllowAny]
    catalog_config = PNEUMATIC_PLUGS_CONFIG
