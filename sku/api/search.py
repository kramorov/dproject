# sku/api/search.py
"""
Публичный поиск моделей каталога по артикулу (SKU.code).

Глобальный поиск на фронте: по вводу артикула возвращает подходящие SKU,
затем по SKU открывается карточка модели-источника.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from django.utils import translation

from sku.models import SKU
from price.services.currency_converter import get_display_price
from core.utils.catalog_helpers import get_currency_code


class SKUSearchView(APIView):
    """GET /api/admin/sku/search/?q=... — поиск артикулов по подстроке (без учёта регистра)."""

    permission_classes = [AllowAny]

    def get(self, request):
        q = (request.query_params.get('q') or '').strip()
        if not q:
            return Response({'results': []})

        base = SKU.objects.filter(
            is_active=True,
            source_content_type__isnull=False,
            source_object_id__isnull=False,
        )

        qfold = q.casefold()
        results = []
        seen_ids = set()

        # Быстрый путь: icontains покрывает ASCII-регистр и кириллицу точного регистра.
        fast = (
            base.filter(code__icontains=q)
            .select_related('equipment_type', 'source_content_type')
            .order_by('code')[:50]
        )
        for sku in fast:
            if qfold in sku.code.casefold():
                results.append(sku)
                seen_ids.add(sku.id)
                if len(results) >= 10:
                    break

        # Если не хватило — досматриваем по casefold (кириллица с другим регистром).
        if len(results) < 10:
            qs = base.select_related('equipment_type', 'source_content_type').order_by('code')
            for sku in qs.iterator(chunk_size=500):
                if sku.id in seen_ids:
                    continue
                if qfold in sku.code.casefold():
                    results.append(sku)
                    if len(results) >= 10:
                        break

        out = []
        for sku in results[:10]:
            ct = sku.source_content_type
            out.append({
                'sku_id': sku.id,
                'code': sku.code,
                'name': sku.name,
                'equipment_type_code': sku.equipment_type.code if sku.equipment_type else None,
                'equipment_type_name': sku.equipment_type.name if sku.equipment_type else None,
                'source_object_id': sku.source_object_id,
                'source_content_type': f'{ct.app_label}.{ct.model}' if ct else None,
            })

        return Response({'results': out})


class SKUModelDetailView(APIView):
    """GET /api/admin/sku/model-detail/?sku_id=... — карточка модели-источника по SKU."""

    permission_classes = [AllowAny]

    def get(self, request):
        sku_id = request.query_params.get('sku_id')
        if not sku_id:
            return Response({'error': 'sku_id is required'}, status=400)

        sku = (
            SKU.objects
            .filter(id=sku_id, is_active=True)
            .select_related('equipment_type', 'source_content_type')
            .first()
        )

        if not sku or not sku.source_content_type_id or not sku.source_object_id:
            return Response({'error': 'Model not found'}, status=404)

        model_class = sku.source_content_type.model_class()
        if model_class is None:
            return Response({'error': 'Model not found'}, status=404)

        try:
            obj = model_class.objects.get(pk=sku.source_object_id)
        except model_class.DoesNotExist:
            return Response({'error': 'Model not found'}, status=404)

        if not hasattr(obj, 'to_dict'):
            return Response({'error': 'Model has no catalog serialization'}, status=404)

        lang = request.GET.get('lang', 'ru')
        currency_code = get_currency_code(request)

        try:
            with translation.override(lang):
                data = obj.to_dict()
                data['price'] = get_display_price(sku.code, currency_code)

                category_name = sku.equipment_type.name if sku.equipment_type else None
                try:
                    data['schema'] = model_class.build_schema(
                        data,
                        price_data=data.get('price'),
                        category_name=category_name,
                    )
                except Exception:
                    pass
        except Exception:
            return Response({'error': 'Failed to serialize model'}, status=500)

        return Response(data)
