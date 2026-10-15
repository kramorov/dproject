# pa_controls/catalog/views_posi_detail.py
"""
GET /api/pa-controls/positioners/catalog/<id>/ — карточка позиционера.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.utils import translation

from pa_controls.catalog.posi_config import POSI_CONFIG
from price.services.currency_converter import get_display_price
from core.utils.catalog_helpers import get_currency_code
from core.utils.localization import locale_from_accept_language


class PosiDetailView(APIView):
    permission_classes = [AllowAny]
    config = POSI_CONFIG

    def get(self, request, pk):
        locale = locale_from_accept_language(request.headers.get('Accept-Language'))
        lang = request.GET.get('lang', 'ru')
        currency_code = get_currency_code(request)

        with translation.override(lang):
            item = get_object_or_404(
                self.config.model_class.objects.select_related(
                    *self.config.select_related,
                    'image_gallery', 'model_line__image_gallery',
                ).prefetch_related(
                    'image_gallery__items__image',
                    'tech_docs',
                    'exd_options__explosion_protection_class',
                    'exd_options__hazardous_group',
                    'exd_options__temperature_class',
                    'exd_options__explosion_protection_level',
                    'signal_profile__entries__signal_role',
                    'signal_profile__entries__sensor__signal_type',
                    'signal_profile__entries__input_signal',
                    'model_line__image_gallery__items__image',
                    'model_line__tech_docs',
                ),
                pk=pk,
            )
            data = item.to_dict(locale=locale)

            sku_id = item.sku_id
            if sku_id:
                data['price'] = get_display_price(sku_id, currency_code)

            data['schema'] = self.config.model_class.build_schema(
                data,
                price_data=data.get('price'),
                category_name=self.config.labels.get('title', ''),
            )

        return Response(data)
