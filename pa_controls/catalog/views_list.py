# pa_controls/catalog/views_list.py
"""
GET /api/pa-controls/catalog/ — list with filters, search.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from pa_controls.catalog.config import LIMIT_SWITCH_CONFIG


class LimitSwitchBoxCatalogView(APIView):
    permission_classes = [AllowAny]
    config = LIMIT_SWITCH_CONFIG

    def get(self, request):
        params = request.query_params
        scope = params.get('scope', 'list')
        filter_set = self.config.get_filter_set(scope)

        qs = self.config.get_scoped_queryset()
        qs = self.config.apply_visibility_scope(qs, request)
        qs = qs.select_related(*self.config.select_related)
        qs = qs.prefetch_related(*self.config.prefetch_fields)

        result = self.config.model_class.apply_filters_and_split(
            params,
            filter_definitions=filter_set.definitions,
            base_queryset=qs,
        )

        return Response(result)
