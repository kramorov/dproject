# filter_regulator/catalog/views_detail.py
"""
GET /api/filter-regulator/catalog/<id>/ — detail card.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.utils import translation

from filter_regulator.catalog.config import FILTER_REGULATOR_CONFIG
from price.services.currency_converter import get_display_price
from core.utils.catalog_helpers import get_currency_code


class FilterRegulatorDetailView(APIView):
    permission_classes = [AllowAny]
    config = FILTER_REGULATOR_CONFIG

    def get(self, request, pk):
        lang = request.GET.get('lang', 'ru')
        currency_code = get_currency_code(request)

        with translation.override(lang):
            obj = get_object_or_404(
                self.config.model_class.objects
                .select_related(*self.config.select_related)
                .prefetch_related(*self.config.prefetch_fields),
                pk=pk,
            )
            data = obj.to_dict()

            sku_code = obj.sku.code if hasattr(obj, 'sku') and obj.sku else None
            if sku_code:
                data['price'] = get_display_price(sku_code, currency_code)

            data['schema'] = self.config.model_class.build_schema(
                data,
                price_data=data.get('price'),
                category_name=self.config.labels.get('title', ''),
            )

        return Response(data)
