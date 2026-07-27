# gearbox/catalog/views_engineer_filters.py
"""
GET /api/gearbox/engineer/filters/ — filter options for EngineerSelection.

Uses BaseFilterOptionsView with GEARBOX_CONFIG + default_scope='engineer'.
"""
from core.access import catalog_permission_classes
from core.views import BaseFilterOptionsView
from gearbox.catalog.config import GEARBOX_CONFIG


class GearboxEngineerFilterOptionsView(BaseFilterOptionsView):
    permission_classes = catalog_permission_classes()
    
    catalog_config = GEARBOX_CONFIG
    default_scope = 'engineer'
