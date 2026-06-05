# pneumatic_fittings/catalog/views_engineer.py
"""
GET /api/pneumatic-fittings/engineer/ — engineer selection with filters, search, prices.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import translation

from pneumatic_fittings.catalog.config import PNEUMATIC_FITTINGS_CONFIG
from price.services.currency_converter import get_bulk_prices
from core.utils.catalog_helpers import get_currency_code


class PneumaticFittingsEngineerView(APIView):
    permission_classes = [AllowAny]
    config = PNEUMATIC_FITTINGS_CONFIG

    def get(self, request):
        params = request.query_params
        lang = params.get('lang', 'ru')
        currency_code = get_currency_code(request)
        filter_set = self.config.get_filter_set('engineer')

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
                (item.get('sku') or {}).get('code')
                for item in data
                if (item.get('sku') or {}).get('code')
            ]
            prices = get_bulk_prices(sku_codes, currency_code) if sku_codes else {}
            for item in data:
                item['price'] = prices.get((item.get('sku') or {}).get('code'))

            if result.get('compatible_data'):
                comp_data = result['compatible_data']
                comp_skus = [
                    (item.get('sku') or {}).get('code')
                    for item in comp_data
                    if (item.get('sku') or {}).get('code')
                ]
                comp_prices = get_bulk_prices(comp_skus, currency_code) if comp_skus else {}
                for item in comp_data:
                    item['price'] = comp_prices.get((item.get('sku') or {}).get('code'))

            result['currency'] = currency_code

        return Response(result)
