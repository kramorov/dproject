# price/views/price_snapshot.py
"""
GET /api/admin/prices/snapshot/ — срез последних цен.

Параметры:
    content_type_id   — ID ContentType (обязательно)
    object_ids        — список ID товаров через запятую (обязательно)
    price_variety_id  — фильтр по виду цены (опционально)
    currency_id       — фильтр по валюте (опционально)
    as_of_date        — на какую дату срез (опционально, по умолчанию сегодня)

Логика:
    Для каждого object_id находит последнюю по price_date запись PriceHistory,
    не старше as_of_date. Возвращает словарь {object_id: price_data}.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from price.models import PriceHistory
from django.utils.timezone import now
from django.db.models import Max


class PriceSnapshotView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        ct_id = request.query_params.get('content_type_id')
        if not ct_id:
            return Response({'error': 'content_type_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        object_ids_raw = request.query_params.get('object_ids', '')
        if not object_ids_raw:
            return Response({'error': 'object_ids is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            object_ids = [int(x.strip()) for x in object_ids_raw.split(',') if x.strip()]
        except ValueError:
            return Response({'error': 'object_ids must be comma-separated integers'},
                            status=status.HTTP_400_BAD_REQUEST)

        if not object_ids:
            return Response({'error': 'object_ids is empty'}, status=status.HTTP_400_BAD_REQUEST)

        ct_id = int(ct_id)
        variety_id = request.query_params.get('price_variety_id')
        currency_id = request.query_params.get('currency_id')
        as_of_date = request.query_params.get('as_of_date', now().date().isoformat())

        # Базовый фильтр
        qs = PriceHistory.objects.filter(
            content_type_id=ct_id,
            object_id__in=object_ids,
            is_active=True,
            price_date__lte=as_of_date,
        )

        if variety_id:
            qs = qs.filter(price_variety_id=int(variety_id))
        if currency_id:
            qs = qs.filter(currency_id=int(currency_id))

        # Для каждого object_id находим последнюю цену
        # Подзапрос: макс price_date для каждой комбинации object_id + variety + currency
        snapshots = {}
        for obj_id in object_ids:
            base = qs.filter(object_id=obj_id).order_by('-price_date', '-id')
            entry = base.first()
            if entry:
                snapshots[str(obj_id)] = {
                    'id': entry.id,
                    'object_id': entry.object_id,
                    'price': float(entry.price),
                    'price_variety_id': entry.price_variety_id,
                    'price_variety_name': entry.price_variety.name if entry.price_variety else None,
                    'currency_id': entry.currency_id,
                    'currency_name': entry.currency.name if entry.currency else None,
                    'currency_symbol': entry.currency.symbol if entry.currency else None,
                    'price_date': entry.price_date.isoformat() if entry.price_date else None,
                }
            else:
                snapshots[str(obj_id)] = None

        return Response({
            'content_type_id': ct_id,
            'as_of_date': str(as_of_date),
            'count': len(object_ids),
            'found': sum(1 for v in snapshots.values() if v is not None),
            'snapshots': snapshots,
        })
