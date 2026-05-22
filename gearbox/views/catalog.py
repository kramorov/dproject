# gearbox/views/catalog.py
"""
API каталога редукторов.

GET  /api/gearbox/catalog/       — список с фильтрами и поиском
GET  /api/gearbox/catalog/<id>/  — детальная модель
GET  /api/gearbox/filters/       — опции фильтров
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q, Prefetch
from django.shortcuts import get_object_or_404

from gearbox.models import GearBox
from gearbox.services.filters import (
    GEARBOX_FILTER_DEFINITIONS,
    GEARBOX_SEARCH_FIELDS,
    GEARBOX_SELECT_RELATED,
    GEARBOX_PREFETCH_FIELDS,
)


def _get_image_url(img):
    """URL изображения через API медиабиблиотеки (работает через Vite-прокси /api)."""
    if not img:
        return None
    try:
        return f"/api/media/{img.id}/view/"
    except Exception:
        return None


def _get_file_info(doc):
    """Безопасное получение информации о файле."""
    if not doc:
        return None
    try:
        return {
            'id': doc.id,
            'title': getattr(doc, 'title', '') or '',
            'url': f"/api/media/{doc.id}/download/",
            'file_name': getattr(doc, 'file_name', '') or '',
        }
    except Exception:
        return None


def _serialize_gearbox(obj, include_details=False):
    """
    Сериализация одного редуктора.
    include_details=True — полная информация для страницы товара.
    """
    # --- Изображения ---
    model_images = list(obj.images.all())
    if not model_images:
        model_images = list(obj.model_line.images.all()) if obj.model_line else []

    images_data = []
    for img in model_images:
        url = _get_image_url(img)
        if url:
            images_data.append({
                'id': img.id,
                'title': getattr(img, 'title', '') or '',
                'url': url,
                'preview_url': url,
                'is_default': getattr(img, 'is_default', False),
            })

    # --- alt для изображений ---
    alt_parts = ['Изображение']
    if obj.model_line:
        if obj.model_line.gearbox_output_variety:
            alt_parts.append(obj.model_line.gearbox_output_variety.name)
        if obj.model_line.gearbox_variety:
            alt_parts.append(obj.model_line.gearbox_variety.name)
    if obj.code:
        alt_parts.append(obj.code)
    image_alt = ' '.join(alt_parts)

    # --- Базовая структура ---
    result = {
        'id': obj.id,
        'name': obj.name or '',
        'code': obj.code or '',
        'description': obj.description or '',
        'sorting_order': obj.sorting_order,
        'is_active': obj.is_active,
        'image_alt': image_alt,
        'images': images_data,

        # model_line — кратко
        'model_line': {
            'id': obj.model_line.id,
            'name': obj.model_line.name,
            'code': getattr(obj.model_line, 'code', '') or '',
            'gearbox_output_variety': (
                obj.model_line.gearbox_output_variety.name
                if obj.model_line and obj.model_line.gearbox_output_variety else None
            ),
            'gearbox_variety': (
                obj.model_line.gearbox_variety.name
                if obj.model_line and obj.model_line.gearbox_variety else None
            ),
            'brand': {
                'id': obj.model_line.brand.id,
                'name': obj.model_line.brand.name,
            } if obj.model_line and obj.model_line.brand else None,
        } if obj.model_line else None,

        # SKU (для цен)
        'sku': {
            'id': obj.sku.id,
            'code': obj.sku.code,
            'name': obj.sku.name,
        } if hasattr(obj, 'sku') and obj.sku else None,

        # IP и температуры
        'ip': {'id': obj.ip.id, 'name': obj.ip.name} if obj.ip else None,
        'work_temp_min': obj.work_temp_min,
        'work_temp_max': obj.work_temp_max,

        # Корпус — кратко
        'body': {
            'id': obj.body.id,
            'name': obj.body.name,
            'code': obj.body.code or '',
            'transmission_variety': (
                obj.body.transmission_variety.name
                if obj.body and obj.body.transmission_variety else None
            ),
            'reduction_ratio_text': obj.body.reduction_ratio_text or '',
            'max_output_torque': str(obj.body.max_output_torque) if obj.body and obj.body.max_output_torque else None,
            'weight': str(obj.body.weight) if obj.body and obj.body.weight else None,
        } if obj.body else None,

        'body_material_text': obj.body_material_text or '',
    }

    # --- Детальная информация для страницы товара ---
    if include_details:
        # Изображения model_line (если нет своих)
        if obj.model_line:
            ml_images = list(obj.model_line.images.all())
            for img in ml_images:
                url = _get_image_url(img)
                if url and not any(i['id'] == img.id for i in images_data):
                    images_data.append({
                        'id': img.id,
                        'title': getattr(img, 'title', '') or '',
                        'url': url,
                    })
            result['images'] = images_data

        # Документы: tech_docs модели + tech_docs model_line
        tech_docs = []
        for doc in obj.tech_docs.all():
            info = _get_file_info(doc)
            if info:
                tech_docs.append(info)
        if obj.model_line:
            for doc in obj.model_line.tech_docs.all():
                info = _get_file_info(doc)
                if info and not any(d['id'] == info['id'] for d in tech_docs):
                    tech_docs.append(info)
        result['tech_docs'] = tech_docs

        # Сертификаты из model_line
        cert_docs = []
        if obj.model_line and hasattr(obj.model_line, 'cert_docs'):
            for doc in obj.model_line.cert_docs.all():
                info = _get_file_info(doc)
                if info:
                    cert_docs.append(info)
        result['cert_docs'] = cert_docs

        # Полный корпус
        if obj.body and hasattr(obj.body, 'api_dict'):
            result['body'] = obj.body.api_dict()

        # Дополнительные поля модели
        result.update({
            'override_mechanism': {
                'id': obj.override_mechanism.id,
                'name': obj.override_mechanism.name,
            } if obj.override_mechanism else None,
            'locking_mechanism': {
                'id': obj.locking_mechanism.id,
                'name': obj.locking_mechanism.name,
            } if obj.locking_mechanism else None,
            'is_declutchable': obj.is_declutchable,
            'is_declutchable_display': obj.is_declutchable_display,
            'extra_params': obj.extra_params or {},
        })

    return result


class GearboxCatalogView(APIView):
    """
    GET /api/gearbox/catalog/

    Параметры:
        search              — поиск по code, name, description
        model_line_id       — фильтр по серии
        brand_id            — фильтр по бренду
        ip_id               — фильтр по IP (с ранжированием)
        work_temp_min       — температура от
        work_temp_max       — температура до
        min_work_torque     — рабочий момент не менее
        body_material_id    — материал корпуса
        body_id             — модель корпуса
        mounting_plate_top_id — монтажная площадка
        is_active           — только активные (по умолчанию true)
        limit / offset      — пагинация
    """
    permission_classes = [AllowAny]

    def get(self, request):
        params = request.query_params

        # Базовый queryset с оптимизацией
        qs = GearBox.objects.select_related(*GEARBOX_SELECT_RELATED)
        qs = qs.prefetch_related(*GEARBOX_PREFETCH_FIELDS)

        # Активность (по умолчанию только активные)
        is_active = params.get('is_active', 'true')
        if is_active.lower() in ('true', '1'):
            qs = qs.filter(is_active=True)

        filters_applied = {}

        # Применяем фильтры из GEARBOX_FILTER_DEFINITIONS
        for fd in GEARBOX_FILTER_DEFINITIONS:
            value = params.get(fd.param_name)
            if value is None or value == '' or value == 'all':
                continue

            lookup, converted = fd.build_filter_lookup(value)
            if lookup and converted is not None:
                qs = qs.filter(**{lookup: converted})
                filters_applied[fd.param_name] = value

        # Текстовый поиск
        search = params.get('search', '').strip()
        if search:
            q_obj = Q()
            for field in GEARBOX_SEARCH_FIELDS:
                q_obj |= Q(**{f"{field}__icontains": search})
            qs = qs.filter(q_obj)
            filters_applied['search'] = search

        # Пагинация
        total = qs.count()
        limit = min(int(params.get('limit', 24)), 100)
        offset = max(int(params.get('offset', 0)), 0)
        qs = qs[offset:offset + limit]

        # Сериализация
        data = [_serialize_gearbox(obj) for obj in qs]

        # Собираем коды SKU для запроса цен
        sku_codes = [
            obj.sku.code
            for obj in qs
            if hasattr(obj, 'sku') and obj.sku and obj.sku.code
        ]

        return Response({
            'total': total,
            'count': len(data),
            'limit': limit,
            'offset': offset,
            'filters_applied': filters_applied,
            'sku_codes': sku_codes,
            'data': data,
        })


class GearboxDetailView(APIView):
    """
    GET /api/gearbox/catalog/<id>/

    Полная информация о редукторе: изображения, документы, сертификаты, корпус.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        obj = get_object_or_404(
            GearBox.objects
            .select_related(*GEARBOX_SELECT_RELATED)
            .prefetch_related(*GEARBOX_PREFETCH_FIELDS),
            pk=pk,
        )
        data = _serialize_gearbox(obj, include_details=True)
        return Response(data)


class GearboxFilterOptionsView(APIView):
    """
    GET /api/gearbox/filters/

    Возвращает все доступные опции фильтров.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        result = {}
        for fd in GEARBOX_FILTER_DEFINITIONS:
            if fd.data_source_type.value != 'custom':
                try:
                    options = fd.get_options(GearBox)
                    if options:
                        result[fd.param_name] = {
                            'label': fd.label,
                            'order': fd.order,
                            'options': options,
                        }
                except Exception as e:
                    result[fd.param_name] = {
                        'label': fd.label,
                        'order': fd.order,
                        'options': [],
                        'error': str(e),
                    }
        return Response(result)