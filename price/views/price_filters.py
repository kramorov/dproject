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
from producers.models import Brands
from sku.models import SKU


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

        brands_qs = Brands.objects.filter(is_active=True)
        equipment_type_id = request.query_params.get('equipment_type_id')
        if equipment_type_id:
            # Бренды, у которых есть SKU данного типа оборудования.
            brand_ids = SKU.objects.filter(
                equipment_type_id=equipment_type_id, brand__isnull=False
            ).values_list('brand_id', flat=True).order_by().distinct()
            brands_qs = brands_qs.filter(id__in=brand_ids)

        brands = list(
            brands_qs.values('id', 'name')
            .order_by('name')
        )

        return Response({
            'varieties': varieties,
            'currencies': currencies,
            'equipment_types': equipment_types,
            'brands': brands,
        })