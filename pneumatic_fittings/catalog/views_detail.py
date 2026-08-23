# pneumatic_fittings/catalog/views_detail.py
"""
GET /api/pneumatic-fittings/catalog/<id>/ — fitting detail card.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.utils import translation

from pneumatic_fittings.catalog.config import (
    PNEUMATIC_FITTINGS_CONFIG,
    PNEUMATIC_SILENCERS_CONFIG,
    PNEUMATIC_PLUGS_CONFIG,
)
from price.services.currency_converter import get_display_price
from core.utils.catalog_helpers import get_currency_code


class PneumaticFittingsDetailView(APIView):
    permission_classes = [AllowAny]
    config = PNEUMATIC_FITTINGS_CONFIG

    def get(self, request, pk):
        lang = request.GET.get('lang', 'ru')
        currency_code = get_currency_code(request)

        with translation.override(lang):
            obj = get_object_or_404(
                self.config.get_scoped_queryset()
                .select_related(*self.config.select_related)
                .prefetch_related(*self.config.prefetch_fields),
                pk=pk,
            )
            data = obj.to_dict()

            # Price
            sku_code = obj.sku.code if hasattr(obj, 'sku') and obj.sku else None
            if sku_code:
                data['price'] = get_display_price(sku_code, currency_code)

            # Schema.org Product
            data['schema'] = self.config.model_class.build_schema(
                data,
                price_data=data.get('price'),
                category_name=self.config.labels.get('title', ''),
            )

        return Response(data)


class PneumaticSilencersDetailView(PneumaticFittingsDetailView):
    """Карточка глушителя — детали только в пределах вида каталога."""

    config = PNEUMATIC_SILENCERS_CONFIG


class PneumaticPlugsDetailView(PneumaticFittingsDetailView):
    """Карточка заглушки — детали только в пределах вида каталога."""

    config = PNEUMATIC_PLUGS_CONFIG
