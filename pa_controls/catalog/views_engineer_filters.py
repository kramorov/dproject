# pa_controls/catalog/views_engineer_filters.py
"""
GET /api/pa-controls/engineer/filters/ — filter options for EngineerSelection.

Uses BaseFilterOptionsView with LIMIT_SWITCH_CONFIG + default_scope='engineer'.
"""
from project_customers.permissions import SectionAccessPermission
from core.views import BaseFilterOptionsView
from pa_controls.catalog.config import LIMIT_SWITCH_CONFIG


class LimitSwitchBoxEngineerFilterOptionsView(BaseFilterOptionsView):
    permission_classes = [SectionAccessPermission]
    required_section = 'configurator'
    catalog_config = LIMIT_SWITCH_CONFIG
    default_scope = 'engineer'
