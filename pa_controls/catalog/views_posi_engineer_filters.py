# pa_controls/catalog/views_posi_engineer_filters.py
"""
GET /api/pa-controls/positioners/engineer/filters/ — опции фильтров EngineerSelection.
"""
from core.access import catalog_permission_classes
from core.views import BaseFilterOptionsView
from pa_controls.catalog.posi_config import POSI_CONFIG


class PosiEngineerFilterOptionsView(BaseFilterOptionsView):
    permission_classes = catalog_permission_classes()

    catalog_config = POSI_CONFIG
    default_scope = 'engineer'
