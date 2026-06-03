# gearbox/catalog/views_engineer_filters.py
"""
GET /api/gearbox/engineer/filters/ — filter options for EngineerSelection.

Uses BaseFilterOptionsView with GEARBOX_CONFIG + default_scope='engineer'.
"""
from rest_framework.permissions import AllowAny
from core.views import BaseFilterOptionsView
from gearbox.catalog.config import GEARBOX_CONFIG


class GearboxEngineerFilterOptionsView(BaseFilterOptionsView):
    permission_classes = [AllowAny]
    catalog_config = GEARBOX_CONFIG
    default_scope = 'engineer'
