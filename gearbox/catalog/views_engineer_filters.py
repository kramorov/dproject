# gearbox/catalog/views_engineer_filters.py
"""
GET /api/gearbox/engineer/filters/ — filter options for EngineerSelection.

Uses BaseFilterOptionsView with GEARBOX_CONFIG + default_scope='engineer'.
"""
from project_customers.permissions import SectionAccessPermission
from core.views import BaseFilterOptionsView
from gearbox.catalog.config import GEARBOX_CONFIG


class GearboxEngineerFilterOptionsView(BaseFilterOptionsView):
    permission_classes = [SectionAccessPermission]
    required_section = 'configurator'
    catalog_config = GEARBOX_CONFIG
    default_scope = 'engineer'
