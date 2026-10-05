# pa_controls/catalog/views_list.py
"""
GET /api/pa-controls/catalog/ — list with filters, search.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from pa_controls.catalog.config import LIMIT_SWITCH_CONFIG
from price.services.currency_converter import get_bulk_prices
from core.utils.catalog_helpers import get_currency_code
from core.utils.localization import locale_from_accept_language


class LimitSwitchBoxCatalogView(APIView):
    permission_classes = [AllowAny]
    config = LIMIT_SWITCH_CONFIG

    def get(self, request):
        locale = locale_from_accept_language(request.headers.get('Accept-Language'))
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
            locale=locale,
        )

        # Цены
        currency_code = get_currency_code(request)
        data = result.get('data', [])
        sku_ids = [item.get('sku', {}).get('id') for item in data if item.get('sku', {}).get('id')]
        prices = get_bulk_prices(sku_ids, currency_code) if sku_ids else {}
        for item in data:
            item['price'] = prices.get(item.get('sku', {}).get('id'))
        if result.get('compatible_data'):
            comp_data = result['compatible_data']
            comp_sku_ids = [item.get('sku', {}).get('id') for item in comp_data if item.get('sku', {}).get('id')]
            comp_prices = get_bulk_prices(comp_sku_ids, currency_code) if comp_sku_ids else {}
            for item in comp_data:
                item['price'] = comp_prices.get(item.get('sku', {}).get('id'))
            result['currency'] = currency_code

        return Response(result)
