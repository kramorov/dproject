# price/views/price_filters.py
"""
GET /api/admin/prices/filters/ — опции фильтров для каталога цен.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from price.models import PriceHistory, PriceVariety, Currency


class PriceFilterOptionsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        variety_ids = PriceHistory.objects.values_list('price_variety_id', flat=True).distinct()
        varieties = list(PriceVariety.objects.filter(id__in=variety_ids, is_active=True).values('id', 'name', 'code'))

        currency_ids = PriceHistory.objects.values_list('currency_id', flat=True).distinct()
        currencies = list(Currency.objects.filter(id__in=currency_ids, is_active=True).values('id', 'name', 'code', 'symbol'))

        return Response({'price_variety_id': varieties, 'currency_id': currencies})
