# price/views/price_snapshot.py
"""
GET /api/admin/prices/snapshot/ — срез последних цен.

Три режима поиска (определяется по входным параметрам):

1. По GFK (привязанные к сущностям Django):
       ?content_type_id=X&object_ids=1,2,3

2. По коду (номенклатура без сущности — для счетов и КП):
       ?code=RD7,RD7.LT,SB10-2N

3. Если не переданы ни content_type_id+object_ids, ни code — 400 ошибка.

Общие фильтры:
    price_variety_id  — фильтр по виду цены (опционально)
    currency_id       — фильтр по валюте (опционально)
    as_of_date        — на какую дату срез (опционально, по умолчанию сегодня)

Логика:
    Для каждого идентификатора (object_id или code) находит последнюю
    по price_date запись PriceHistory не старше as_of_date.
    Возвращает словарь {key: price_data | null}.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from price.models import PriceHistory
from django.utils.timezone import now


class PriceSnapshotView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        ct_id = request.query_params.get('content_type_id')
        object_ids_raw = request.query_params.get('object_ids', '')
        code_raw = request.query_params.get('code', '')

        # ── Определяем режим ──
        is_gfk = bool(ct_id and object_ids_raw)
        is_code = bool(code_raw)

        if not is_gfk and not is_code:
            return Response(
                {'error': 'Укажите content_type_id+object_ids (поиск по сущности) или code (поиск по коду)'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Общие фильтры ──
        variety_id = request.query_params.get('price_variety_id')
        currency_id = request.query_params.get('currency_id')
        as_of_date = request.query_params.get('as_of_date', now().date().isoformat())

        base_qs = PriceHistory.objects.filter(
            is_active=True,
            price_date__lte=as_of_date,
        )
        if variety_id:
            base_qs = base_qs.filter(price_variety_id=int(variety_id))
        if currency_id:
            base_qs = base_qs.filter(currency_id=int(currency_id))

        # ── Режим 1: GFK (сущности Django) ──
        if is_gfk:
            try:
                object_ids = [int(x.strip()) for x in object_ids_raw.split(',') if x.strip()]
            except ValueError:
                return Response(
                    {'error': 'object_ids must be comma-separated integers'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not object_ids:
                return Response({'error': 'object_ids is empty'}, status=status.HTTP_400_BAD_REQUEST)

            ct_id = int(ct_id)
            qs = base_qs.filter(content_type_id=ct_id, object_id__in=object_ids)

            snapshots = {}
            for obj_id in object_ids:
                entry = qs.filter(object_id=obj_id).order_by('-price_date', '-id').first()
                snapshots[str(obj_id)] = self._format_entry(entry) if entry else None

            return Response({
                'mode': 'gfk',
                'content_type_id': ct_id,
                'as_of_date': str(as_of_date),
                'count': len(object_ids),
                'found': sum(1 for v in snapshots.values() if v is not None),
                'snapshots': snapshots,
            })

        # ── Режим 2: по коду (номенклатура) ──
        codes = [c.strip() for c in code_raw.split(',') if c.strip()]
        if not codes:
            return Response({'error': 'code is empty'}, status=status.HTTP_400_BAD_REQUEST)

        qs = base_qs.filter(code__in=codes)

        snapshots = {}
        for code in codes:
            entry = qs.filter(code=code).order_by('-price_date', '-id').first()
            snapshots[code] = self._format_entry(entry) if entry else None

        return Response({
            'mode': 'code',
            'as_of_date': str(as_of_date),
            'count': len(codes),
            'found': sum(1 for v in snapshots.values() if v is not None),
            'snapshots': snapshots,
        })

    # ── Форматирование ──

    def _format_entry(self, entry):
        """Форматирует одну запись PriceHistory для ответа."""
        return {
            'id': entry.id,
            'code': entry.code,
            'name': entry.name,
            'object_id': entry.object_id,
            'content_type_id': entry.content_type_id,
            'price': float(entry.price),
            'price_variety_id': entry.price_variety_id,
            'price_variety_name': entry.price_variety.name if entry.price_variety else None,
            'currency_id': entry.currency_id,
            'currency_name': entry.currency.name if entry.currency else None,
            'currency_symbol': entry.currency.symbol if entry.currency else None,
            'price_date': entry.price_date.isoformat() if entry.price_date else None,
        }
