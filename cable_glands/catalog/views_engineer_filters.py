# cable_glands/catalog/views_engineer_filters.py
"""
GET /api/cable-glands/engineer/filters/ — опции фильтров инженерного подбора.
"""
from core.access import catalog_permission_classes
from core.views import BaseFilterOptionsView
from cable_glands.catalog.config import CABLE_GLAND_CONFIG


class CableGlandEngineerFilterOptionsView(BaseFilterOptionsView):
    permission_classes = catalog_permission_classes()

    catalog_config = CABLE_GLAND_CONFIG
    default_scope = 'engineer'
