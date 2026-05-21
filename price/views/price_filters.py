# price/views/price_filters.py
"""
GET /api/admin/prices/filters/ — опции фильтров для каталога цен.

Возвращает:
    varieties       — все активные виды цен
    currencies      — все активные валюты
    equipment_types — типы оборудования с content_type_id (для создания документов)
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from price.models import PriceVariety, Currency
from core.models.equipment_type import EquipmentType


class PriceFilterOptionsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        varieties = list(
            PriceVariety.objects.filter(is_active=True)
            .values('id', 'name', 'code')
        )

        currencies = list(
            Currency.objects.filter(is_active=True)
            .values('id', 'name', 'code', 'symbol')
        )

        equipment_types = list(
            EquipmentType.objects.filter(is_active=True, content_type__isnull=False)
            .values('id', 'name', 'content_type_id')
            .order_by('name')
        )

        return Response({
            'varieties': varieties,
            'currencies': currencies,
            'equipment_types': equipment_types,
        })
