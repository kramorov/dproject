# price/views/document_detail.py
"""
GET/PUT/DELETE /api/admin/prices/documents/<id>/ — редактирование документа
POST /api/admin/prices/documents/<id>/apply/ — применить цены
GET/POST/DELETE /api/admin/prices/documents/<id>/items/ — строки документа
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from price.models import PriceDocument, PriceDocumentItem, Currency, PriceVariety
from django.contrib.contenttypes.models import ContentType


class PriceDocumentDetailView(APIView):
    permission_classes = [AllowAny]

    def _get_doc(self, pk):
        try:
            return PriceDocument.objects.prefetch_related('items__content_type', 'items__price_variety', 'items__currency').get(pk=pk)
        except PriceDocument.DoesNotExist:
            return None

    def get(self, request, pk):
        doc = self._get_doc(pk)
        if not doc:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        items = []
        for item in doc.items.filter(is_active=True):
            items.append({
                'id': item.id,
                'object_id': item.object_id,
                'content_type_id': item.content_type_id,
                'price': float(item.price),
                'price_variety_id': item.price_variety_id,
                'price_variety_name': item.price_variety.name if item.price_variety else None,
                'currency_id': item.currency_id,
                'currency_name': item.currency.name if item.currency else None,
                'comment': item.comment,
                'sorting_order': item.sorting_order,
            })

        return Response({
            'id': doc.id,
            'name': doc.name,
            'document_date': doc.document_date.isoformat(),
            'description': doc.description,
            'is_applied': doc.is_applied,
            'item_content_type_id': doc.item_content_type_id,
            'item_content_type_name': str(doc.item_content_type) if doc.item_content_type else None,
            'items': items,
        })

    def put(self, request, pk):
        doc = self._get_doc(pk)
        if not doc:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        if doc.is_applied:
            return Response({'error': 'Document already applied'}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data
        if 'name' in data:
            doc.name = data['name'].strip()
        if 'description' in data:
            doc.description = data['description']
        if 'document_date' in data:
            doc.document_date = data['document_date']
        doc.save()
        return Response({'success': True})

    def delete(self, request, pk):
        doc = self._get_doc(pk)
        if not doc:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        doc.delete()
        return Response({'success': True})

    # ── Apply ──
    def post(self, request, pk):
        """POST /api/admin/prices/documents/<id>/apply/ — применить цены."""
        doc = self._get_doc(pk)
        if not doc:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        if doc.is_applied:
            return Response({'error': 'Already applied'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            doc.apply_prices()
            return Response({'success': True, 'items_processed': doc.items.count()})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PriceDocumentItemView(APIView):
    """GET/POST/DELETE /api/admin/prices/documents/<doc_id>/items/"""
    permission_classes = [AllowAny]

    def get(self, request, doc_id):
        try:
            doc = PriceDocument.objects.get(pk=doc_id)
        except PriceDocument.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        items = doc.items.filter(is_active=True).order_by('sorting_order')
        data = []
        for item in items:
            data.append({
                'id': item.id,
                'object_id': item.object_id,
                'content_type_id': item.content_type_id,
                'price': float(item.price),
                'price_variety_id': item.price_variety_id,
                'currency_id': item.currency_id,
                'comment': item.comment,
                'sorting_order': item.sorting_order,
            })
        return Response(data)

    def post(self, request, doc_id):
        try:
            doc = PriceDocument.objects.get(pk=doc_id)
        except PriceDocument.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        if doc.is_applied:
            return Response({'error': 'Document already applied'}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data
        object_id = data.get('object_id')
        if not object_id:
            return Response({'error': 'object_id required'}, status=status.HTTP_400_BAD_REQUEST)

        item = PriceDocumentItem.objects.create(
            document=doc,
            content_type=doc.item_content_type,
            object_id=int(object_id),
            price_variety_id=data.get('price_variety_id'),
            currency_id=data.get('currency_id'),
            price=data.get('price', 0),
            comment=data.get('comment', ''),
            sorting_order=data.get('sorting_order', 0),
        )
        return Response({'id': item.id}, status=status.HTTP_201_CREATED)

    def delete(self, request, doc_id):
        item_id = request.query_params.get('id')
        if not item_id:
            return Response({'error': 'id param required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = PriceDocumentItem.objects.get(pk=int(item_id), document_id=doc_id)
        except PriceDocumentItem.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        item.delete()
        return Response({'success': True})
