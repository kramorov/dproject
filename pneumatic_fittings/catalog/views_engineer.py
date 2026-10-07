# pneumatic_fittings/catalog/views_engineer.py
"""
GET /api/pneumatic-fittings/engineer/ — engineer selection with filters, search, prices.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from core.access import catalog_permission_classes
from django.utils import translation

from pneumatic_fittings.catalog.config import (
    PNEUMATIC_FITTINGS_CONFIG,
    PNEUMATIC_SILENCERS_CONFIG,
    PNEUMATIC_PLUGS_CONFIG,
)
from price.services.currency_converter import get_bulk_prices
from core.utils.catalog_helpers import get_currency_code
from core.utils.localization import locale_from_accept_language


class PneumaticFittingsEngineerView(APIView):
    permission_classes = catalog_permission_classes()
    
    config = PNEUMATIC_FITTINGS_CONFIG

    def get(self, request):
        params = request.query_params
        lang = params.get('lang', 'ru')
        locale = locale_from_accept_language(request.headers.get('Accept-Language'))
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
                locale=locale,
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


class PneumaticSilencersEngineerView(PneumaticFittingsEngineerView):
    """Инженерный подбор глушителей — тот же механизм, другой вид."""

    config = PNEUMATIC_SILENCERS_CONFIG


class PneumaticPlugsEngineerView(PneumaticFittingsEngineerView):
    """Инженерный подбор заглушек — тот же механизм, другой вид."""

    config = PNEUMATIC_PLUGS_CONFIG
