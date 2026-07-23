# price/views/price_catalog.py
"""
GET /api/admin/prices/ — каталог цен с фильтрацией.

Параметры:
    search        — поиск по name, code
    price_variety_id — фильтр по виду цены
    currency_id   — фильтр по валюте
    date_from     — цены c даты
    date_to       — цены до даты
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from project_customers.permissions import SectionAccessPermission
from price.models import PriceHistory


class PriceCatalogView(APIView):
    permission_classes = [SectionAccessPermission]
    required_section = 'admin_section'

    def get(self, request):
        qs = PriceHistory.objects.filter(is_active=True).select_related('price_variety', 'currency', 'content_type')

        variety = request.query_params.get('price_variety_id')
        if variety:
            qs = qs.filter(price_variety_id=int(variety))

        currency = request.query_params.get('currency_id')
        if currency:
            qs = qs.filter(currency_id=int(currency))

        date_from = request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(price_date__gte=date_from)

        date_to = request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(price_date__lte=date_to)

        equipment_type_id = request.query_params.get('equipment_type_id')
        if equipment_type_id:
            qs = qs.filter(sku__equipment_type_id=int(equipment_type_id))

        brand_id = request.query_params.get('brand_id')
        if brand_id:
            qs = qs.filter(sku__brand_id=int(brand_id))

        search = request.query_params.get('search', '').strip()
        if search:
            from django.db.models import Q
            qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))

        is_current = request.query_params.get('is_current')
        if is_current is not None:
            qs = qs.filter(is_current=is_current.lower() in ('true', '1'))

        total = qs.count()
        limit = int(request.query_params.get('limit', 100))
        offset = int(request.query_params.get('offset', 0))
        qs = qs[offset:offset + limit]

        data = []
        for ph in qs:
            data.append({
                'id': ph.id,
                'name': ph.name,
                'code': ph.code,
                'price': float(ph.price),
                'price_variety': {'id': ph.price_variety_id, 'name': ph.price_variety.name} if ph.price_variety else None,
                'currency': {'id': ph.currency_id, 'name': ph.currency.name, 'symbol': ph.currency.symbol} if ph.currency else None,
                'price_date': ph.price_date.isoformat() if ph.price_date else None,
                'is_current': ph.is_current,
                'object_id': ph.object_id,
                'content_type_id': ph.content_type_id,
            })

        return Response({'total': total, 'count': len(data), 'data': data})
