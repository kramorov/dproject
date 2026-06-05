# price/views/document_detail.py
"""
GET/PUT/DELETE /api/admin/prices/documents/<id>/ — редактирование документа
POST /api/admin/prices/documents/<id>/apply/ — провести (записать цены в PriceHistory)
POST /api/admin/prices/documents/<id>/unapply/ — отмена проведения
GET/POST/DELETE /api/admin/prices/documents/<id>/items/ — строки документа
GET /api/admin/prices/documents/<id>/export/ — экспорт в Excel
POST /api/admin/prices/documents/<id>/import/ — импорт из Excel
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.http import HttpResponse
from price.models import PriceDocument, PriceDocumentItem, Currency, PriceVariety
from price.services.excel_io import export_document_to_excel, import_document_from_excel


class PriceDocumentDetailView(APIView):
    permission_classes = [AllowAny]

    def _get_doc(self, pk):
        try:
            return PriceDocument.objects.select_related(
                'default_price_variety', 'default_currency'
            ).prefetch_related(
                'items__sku', 'items__price_variety', 'items__currency'
            ).get(pk=pk)
        except PriceDocument.DoesNotExist:
            return None

    def get(self, request, pk):
        doc = self._get_doc(pk)
        if not doc:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        items_qs = list(doc.items.filter(is_active=True).select_related('sku'))

        items = []
        for item in items_qs:
            items.append({
                'id': item.id,
                'sku_id': item.sku_id,
                'product_code': item.sku.code if item.sku else '',
                'product_name': item.sku.name if item.sku else '',
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
            'status': doc.status,
            'status_label': doc.get_status_display(),
            'is_applied': doc.is_applied,
            'default_price_variety_id': doc.default_price_variety_id,
            'default_price_variety_name': doc.default_price_variety.name if doc.default_price_variety else None,
            'default_currency_id': doc.default_currency_id,
            'default_currency_name': doc.default_currency.name if doc.default_currency else None,
            'default_currency_symbol': doc.default_currency.symbol if doc.default_currency else None,
            'items': items,
        })

    def put(self, request, pk):
        """
        PUT — редактировать реквизиты документа.

        Реквизиты (name, date) — только в статусе draft.
        Статус можно менять: draft → on_approval (только перевод).
        """
        doc = self._get_doc(pk)
        if not doc:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data

        # Изменение статуса (разрешено draft→on_approval)
        if 'status' in data:
            new_status = data['status']
            if doc.status == PriceDocument.Status.DRAFT and new_status == PriceDocument.Status.ON_APPROVAL:
                doc.status = PriceDocument.Status.ON_APPROVAL
                doc.save(update_fields=['status'])
                return Response({'success': True, 'status': doc.status, 'status_label': doc.get_status_display()})
            else:
                return Response(
                    {'error': f'Переход {doc.status} → {new_status} запрещён'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Редактирование реквизитов — только draft
        if doc.status != PriceDocument.Status.DRAFT:
            return Response(
                {'error': f'Редактирование запрещено. Текущий статус: {doc.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if 'name' in data:
            doc.name = data['name'].strip()
        if 'description' in data:
            doc.description = data['description']
        if 'document_date' in data:
            doc.document_date = data['document_date']
        if 'default_price_variety_id' in data:
            pv_id = data['default_price_variety_id']
            doc.default_price_variety_id = int(pv_id) if pv_id else None
        if 'default_currency_id' in data:
            cur_id = data['default_currency_id']
            doc.default_currency_id = int(cur_id) if cur_id else None

        doc.save()
        return Response({'success': True})

    def delete(self, request, pk):
        doc = self._get_doc(pk)
        if not doc:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        doc.delete()
        return Response({'success': True})

    # ── Apply (проведение) ──
    def post(self, request, pk):
        """
        POST /api/admin/prices/documents/<id>/apply/ — провести документ.
        POST /api/admin/prices/documents/<id>/unapply/ — отмена проведения.
        """
        doc = self._get_doc(pk)
        if not doc:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        action = request.path.rstrip('/').split('/')[-1]

        if action == 'apply':
            if doc.status == PriceDocument.Status.POSTED:
                return Response({'error': 'Документ уже проведён'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                doc.apply_prices()
                return Response({
                    'success': True,
                    'items_processed': doc.items.filter(is_active=True).count(),
                    'status': doc.status,
                    'status_label': doc.get_status_display(),
                })
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif action == 'unapply':
            if doc.status != PriceDocument.Status.POSTED:
                return Response({'error': 'Документ не был проведён'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                doc.unapply_prices()
                return Response({
                    'success': True,
                    'status': doc.status,
                    'status_label': doc.get_status_display(),
                })
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'error': 'Unknown action'}, status=status.HTTP_400_BAD_REQUEST)


class PriceDocumentItemView(APIView):
    """GET/POST/DELETE /api/admin/prices/documents/<doc_id>/items/"""
    permission_classes = [AllowAny]

    def get(self, request, doc_id):
        try:
            doc = PriceDocument.objects.get(pk=doc_id)
        except PriceDocument.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        items = doc.items.filter(is_active=True).select_related('sku').order_by('sorting_order')
        data = []
        for item in items:
            data.append({
                'id': item.id,
                'sku_id': item.sku_id,
                'product_code': item.sku.code if item.sku else '',
                'product_name': item.sku.name if item.sku else '',
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

        if doc.status != PriceDocument.Status.DRAFT:
            return Response(
                {'error': f'Добавление позиций запрещено. Статус: {doc.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        sku_id = request.data.get('sku_id')
        if not sku_id:
            return Response({'error': 'sku_id required'}, status=status.HTTP_400_BAD_REQUEST)

        price_variety = doc.default_price_variety
        currency = doc.default_currency

        item = PriceDocumentItem.objects.create(
            document=doc,
            sku_id=sku_id,
            price=request.data.get('price', 0),
            price_variety=price_variety,
            currency=currency,
            comment=request.data.get('comment', ''),
        )

        return Response({
            'id': item.id,
            'sku_id': item.sku_id,
            'product_code': item.sku.code if item.sku else '',
            'product_name': item.sku.name if item.sku else '',
            'price': float(item.price),
            'price_variety_id': item.price_variety_id,
            'currency_id': item.currency_id,
            'comment': item.comment,
        }, status=status.HTTP_201_CREATED)

    def delete(self, request, doc_id):
        try:
            doc = PriceDocument.objects.get(pk=doc_id)
        except PriceDocument.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        item_id = request.query_params.get('id')
        if not item_id:
            return Response({'error': 'id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = doc.items.get(pk=item_id)
        except PriceDocumentItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

        item.delete()
        return Response({'success': True})


class PriceDocumentExportView(APIView):
    """GET /api/admin/prices/documents/<pk>/export/ — скачать Excel"""
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            doc = PriceDocument.objects.get(pk=pk)
        except PriceDocument.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            output = export_document_to_excel(doc)
            safe_name = doc.name.replace(' ', '_').replace('/', '-')[:50] if doc.name else 'export'
            response = HttpResponse(
                output.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
            response['Content-Disposition'] = f'attachment; filename="price_doc_{doc.pk}_{safe_name}.xlsx"'
            return response
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PriceDocumentImportView(APIView):
    """POST /api/admin/prices/documents/<pk>/import/ — загрузить Excel"""
    permission_classes = [AllowAny]

    def post(self, request, pk):
        try:
            doc = PriceDocument.objects.get(pk=pk)
        except PriceDocument.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        if doc.status != PriceDocument.Status.DRAFT:
            return Response(
                {'error': f'Импорт запрещён. Статус: {doc.get_status_display()}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = import_document_from_excel(doc, uploaded)
            return Response({
                'success': True,
                'created': result['created'],
                'updated': result['updated'],
                'errors': result['errors'],
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
