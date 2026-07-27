# gearbox/catalog/views_engineer.py
"""
GET /api/gearbox/engineer/ — engineer selection with filters, search, prices.

Dedicated endpoint for EngineerSelection component.
Uses GEARBOX_CONFIG with scope='engineer'.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from core.access import catalog_permission_classes
from django.utils import translation

from gearbox.catalog.config import GEARBOX_CONFIG
from price.services.currency_converter import get_bulk_prices
from core.utils.catalog_helpers import get_currency_code


class GearboxEngineerView(APIView):
    permission_classes = catalog_permission_classes()
    
    config = GEARBOX_CONFIG

    def get(self, request):
        params = request.query_params
        lang = params.get('lang', 'ru')
        currency_code = get_currency_code(request)
        filter_set = self.config.get_filter_set('engineer')

        with translation.override(lang):
            # ── Layer 0: visibility scope ──
            qs = self.config.get_scoped_queryset()
            qs = self.config.apply_visibility_scope(qs, request)
            qs = qs.select_related(*self.config.select_related)
            qs = qs.prefetch_related(*self.config.prefetch_fields)

            # ── Layer 1+2: filters + optional split ──
            result = self.config.model_class.apply_filters_and_split(
                params,
                filter_definitions=filter_set.definitions,
                base_queryset=qs,
            )

            # ── Prices ──
            data = result['data']
            sku_codes = [
                item.get('sku', {}).get('code')
                for item in data
                if item.get('sku', {}).get('code')
            ]
            prices = get_bulk_prices(sku_codes, currency_code) if sku_codes else {}
            for item in data:
                item['price'] = prices.get(item.get('sku', {}).get('code'))

            if result.get('compatible_data'):
                comp_data = result['compatible_data']
                comp_skus = [
                    item.get('sku', {}).get('code')
                    for item in comp_data
                    if item.get('sku', {}).get('code')
                ]
                comp_prices = get_bulk_prices(comp_skus, currency_code) if comp_skus else {}
                for item in comp_data:
                    item['price'] = comp_prices.get(item.get('sku', {}).get('code'))

            result['currency'] = currency_code

        return Response(result)
