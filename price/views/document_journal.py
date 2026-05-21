# price/views/document_journal.py
"""
GET /api/admin/prices/documents/ — журнал документов цен.

Параметры:
    search         — поиск по названию
    date_from/date_to — по дате документа
    status         — фильтр по статусу (draft/on_approval/posted)
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from price.models import PriceDocument


class PriceDocumentListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = PriceDocument.objects.filter(is_active=True).prefetch_related('items')

        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(name__icontains=search)

        date_from = request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(document_date__gte=date_from)

        date_to = request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(document_date__lte=date_to)

        st = request.query_params.get('status', '').strip()
        if st:
            qs = qs.filter(status=st)

        # обратная совместимость: ?is_applied=true → status=posted
        is_applied = request.query_params.get('is_applied')
        if is_applied is not None:
            if is_applied.lower() in ('true', '1'):
                qs = qs.filter(status='posted')
            else:
                qs = qs.exclude(status='posted')

        total = qs.count()
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        qs = qs[offset:offset + limit]

        data = []
        for doc in qs:
            data.append({
                'id': doc.id,
                'name': doc.name,
                'document_date': doc.document_date.isoformat(),
                'description': doc.description,
                'status': doc.status,
                'status_label': doc.get_status_display(),
                'is_applied': doc.is_applied,
                'items_count': doc.items.filter(is_active=True).count(),
                'content_type_id': doc.item_content_type_id,
                'content_type_name': str(doc.item_content_type) if doc.item_content_type else None,
                'default_price_variety_id': doc.default_price_variety_id,
                'default_price_variety_name': doc.default_price_variety.name if doc.default_price_variety else None,
                'default_currency_id': doc.default_currency_id,
                'default_currency_name': doc.default_currency.name if doc.default_currency else None,
            })

        return Response({'total': total, 'count': len(data), 'data': data})

    def post(self, request):
        from django.contrib.contenttypes.models import ContentType
        data = request.data
        name = data.get('name', '').strip()
        if not name:
            return Response({'error': 'name is required'}, status=status.HTTP_400_BAD_REQUEST)

        ct_id = data.get('item_content_type_id')
        if not ct_id:
            return Response({'error': 'item_content_type_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ct = ContentType.objects.get(pk=int(ct_id))
        except ContentType.DoesNotExist:
            return Response({'error': 'ContentType not found'}, status=status.HTTP_400_BAD_REQUEST)

        doc = PriceDocument.objects.create(
            name=name,
            item_content_type=ct,
            document_date=data.get('document_date') or None,
            description=data.get('description', ''),
            default_price_variety_id=data.get('default_price_variety_id') or None,
            default_currency_id=data.get('default_currency_id') or None,
        )
        return Response({
            'id': doc.id,
            'name': doc.name,
            'document_date': str(doc.document_date),
            'status': doc.status,
            'status_label': doc.get_status_display(),
        }, status=status.HTTP_201_CREATED)
