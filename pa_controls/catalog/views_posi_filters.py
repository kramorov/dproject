# pa_controls/catalog/views_posi_filters.py
"""
GET /api/pa-controls/positioners/filters/ — опции фильтров для FilterSidebar.
"""
from rest_framework.permissions import AllowAny
from core.views import BaseFilterOptionsView
from pa_controls.catalog.posi_config import POSI_CONFIG


class PosiFilterOptionsView(BaseFilterOptionsView):
    permission_classes = [AllowAny]
    catalog_config = POSI_CONFIG
