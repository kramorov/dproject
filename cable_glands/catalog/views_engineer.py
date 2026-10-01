# cable_glands/catalog/views_engineer.py
"""
GET /api/cable-glands/engineer/ — инженерный подбор с фильтрами, поиском, ценами.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from core.access import catalog_permission_classes
from django.utils import translation

from cable_glands.catalog.config import CABLE_GLAND_CONFIG
from price.services.currency_converter import get_bulk_prices
from core.utils.catalog_helpers import get_currency_code


class CableGlandEngineerView(APIView):
    permission_classes = catalog_permission_classes()

    config = CABLE_GLAND_CONFIG

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
            sku_ids = [
                (item.get('sku') or {}).get('id')
                for item in data
                if (item.get('sku') or {}).get('id')
            ]
            prices = get_bulk_prices(sku_ids, currency_code) if sku_ids else {}
            for item in data:
                item['price'] = prices.get((item.get('sku') or {}).get('id'))

            if result.get('compatible_data'):
                comp_data = result['compatible_data']
                comp_sku_ids = [
                    (item.get('sku') or {}).get('id')
                    for item in comp_data
                    if (item.get('sku') or {}).get('id')
                ]
                comp_prices = get_bulk_prices(comp_sku_ids, currency_code) if comp_sku_ids else {}
                for item in comp_data:
                    item['price'] = comp_prices.get((item.get('sku') or {}).get('id'))

            result['currency'] = currency_code

        return Response(result)
