# pa_controls/catalog/views_engineer_filters.py
"""
GET /api/pa-controls/engineer/filters/ — filter options for EngineerSelection.

Uses BaseFilterOptionsView with LIMIT_SWITCH_CONFIG + default_scope='engineer'.
"""
from core.access import catalog_permission_classes
from core.views import BaseFilterOptionsView
from pa_controls.catalog.config import LIMIT_SWITCH_CONFIG


class LimitSwitchBoxEngineerFilterOptionsView(BaseFilterOptionsView):
    permission_classes = catalog_permission_classes()
    
    catalog_config = LIMIT_SWITCH_CONFIG
    default_scope = 'engineer'
