# cable_glands/catalog/views_list.py
"""
GET /api/cable-glands/catalog/ — список кабельных вводов с фильтрами, поиском, ценами.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import translation

from cable_glands.catalog.config import CABLE_GLAND_CONFIG
from price.services.currency_converter import get_bulk_prices
from core.utils.catalog_helpers import get_currency_code
from core.utils.localization import locale_from_accept_language


class CableGlandCatalogView(APIView):
    permission_classes = [AllowAny]
    config = CABLE_GLAND_CONFIG

    def get(self, request):
        params = request.query_params
        lang = params.get('lang', 'ru')
        locale = locale_from_accept_language(request.headers.get('Accept-Language'))
        currency_code = get_currency_code(request)
        scope = params.get('scope', 'list')
        filter_set = self.config.get_filter_set(scope)

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
                locale=locale,
            )

            # ── Prices ──
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
