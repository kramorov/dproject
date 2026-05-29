# filter_regulator/catalog/views_list.py
"""
GET /api/filter-regulator/catalog/ — list with filters, search, prices.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import translation

from filter_regulator.catalog.config import FILTER_REGULATOR_CONFIG
from price.services.currency_converter import get_bulk_prices
from core.utils.catalog_helpers import get_currency_code


class FilterRegulatorCatalogView(APIView):
    permission_classes = [AllowAny]
    config = FILTER_REGULATOR_CONFIG

    def get(self, request):
        params = request.query_params
        lang = params.get('lang', 'ru')
        currency_code = get_currency_code(request)
        scope = params.get('scope', 'list')
        filter_set = self.config.get_filter_set(scope)

        with translation.override(lang):
            qs = self.config.get_scoped_queryset()
            qs = self.config.apply_visibility_scope(qs, request)
            qs = qs.select_related(*self.config.select_related)
            qs = qs.prefetch_related(*self.config.prefetch_fields)

            result = self.config.model_class.apply_filters_and_split(
                params,
                filter_definitions=filter_set.definitions,
                base_queryset=qs,
            )

            data = result['data']
            sku_codes = [
                item.get('sku', {}).get('code')
                for item in data if item.get('sku', {}).get('code')
            ]
            prices = get_bulk_prices(sku_codes, currency_code) if sku_codes else {}
            for item in data:
                item['price'] = prices.get(item.get('sku', {}).get('code'))

            if result.get('compatible_data'):
                for item in result['compatible_data']:
                    code = item.get('sku', {}).get('code')
                    item['price'] = prices.get(code) if code else None

            result['currency'] = currency_code

        return Response(result)
