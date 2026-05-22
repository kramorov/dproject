# sku/views.py
"""
GET  /api/admin/sku/        — список SKU с фильтрами и поиском
POST /api/admin/sku/batch/  — групповая обработка номенклатуры
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db.models import Q
from .models import SKU


class SkuListView(APIView):
    """
    Список SKU с поиском и фильтрацией.

    Параметры:
        search            — поиск по code, name (подстрока)
        brand_id          — фильтр по бренду (null = не указано)
        equipment_type_id — фильтр по типу оборудования (null = не указано)
        is_active         — фильтр по активности (true/false)
        limit, offset     — пагинация
    """
    permission_classes = [AllowAny]

    def get(self, request):
        qs = SKU.objects.select_related('equipment_type', 'brand').all()

        # Поиск по подстроке
        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(Q(code__icontains=search) | Q(name__icontains=search))

        # Фильтры
        brand_id = request.query_params.get('brand_id')
        if brand_id:
            if brand_id == 'null':
                qs = qs.filter(brand__isnull=True)
            else:
                qs = qs.filter(brand_id=int(brand_id))

        eq_type_id = request.query_params.get('equipment_type_id')
        if eq_type_id:
            if eq_type_id == 'null':
                qs = qs.filter(equipment_type__isnull=True)
            else:
                qs = qs.filter(equipment_type_id=int(eq_type_id))

        is_active = request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ('true', '1'))

        # Сортировка
        qs = qs.order_by('code')

        total = qs.count()
        limit = int(request.query_params.get('limit', 100))
        offset = int(request.query_params.get('offset', 0))
        qs = qs[offset:offset + limit]

        data = []
        for sku in qs:
            data.append({
                'id': sku.id,
                'code': sku.code,
                'name': sku.name,
                'description': sku.description or '',
                'equipment_type_id': sku.equipment_type_id,
                'equipment_type_name': sku.equipment_type.name if sku.equipment_type else None,
                'brand_id': sku.brand_id,
                'brand_name': sku.brand.name if sku.brand else None,
                'is_active': sku.is_active,
                'has_source': bool(sku.source_content_type_id and sku.source_object_id),
                'price_count': sku.price_history.count() if hasattr(sku, 'price_history') else 0,
            })

        return Response({'total': total, 'count': len(data), 'data': data})


class SkuBatchUpdateView(APIView):
    """
    Групповая обработка SKU.

    POST /api/admin/sku/batch/
    Body:
        {
            "ids": [1, 2, 3],
            "equipment_type_id": 5,   // опционально
            "brand_id": 7,            // опционально
            "is_active": true         // опционально
        }

    Если поле не передано — значение не меняется.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        ids = request.data.get('ids')
        if not ids or not isinstance(ids, list):
            return Response({'error': 'ids (list) is required'}, status=status.HTTP_400_BAD_REQUEST)

        update_fields = {}

        if 'equipment_type_id' in request.data:
            val = request.data['equipment_type_id']
            update_fields['equipment_type_id'] = val if val else None

        if 'brand_id' in request.data:
            val = request.data['brand_id']
            update_fields['brand_id'] = val if val else None

        if 'is_active' in request.data:
            update_fields['is_active'] = bool(request.data['is_active'])

        if not update_fields:
            return Response({'error': 'No fields to update'}, status=status.HTTP_400_BAD_REQUEST)

        updated = SKU.objects.filter(id__in=ids).update(**update_fields)

        return Response({
            'success': True,
            'updated': updated,
            'fields': list(update_fields.keys()),
        })
