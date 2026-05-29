# pa_controls/views/catalog.py
"""
API каталога блоков концевых выключателей.

GET  /api/pa-controls/sections/      — серии (группировка, счётчики, фото)
GET  /api/pa-controls/catalog/       — список товаров (карточки)
GET  /api/pa-controls/catalog/<id>/  — детальная карточка товара
GET  /api/pa-controls/filters/       — опции фильтров
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Prefetch, Count
from django.shortcuts import get_object_or_404

from core.views import BaseFilterOptionsView
from pa_controls.models.limit_switch import LimitSwitchBox
from pa_controls.models.lsb_model_line import LimitSwitchModelLine
from pa_controls.models.sensor import SensorComponent

SEARCH_FIELDS = ['code', 'name', 'description']
SELECT_RELATED = [
    'model_line', 'model_line__brand',
    'image_gallery', 'model_line__image_gallery',
    'body', 'sensor_variety', 'primary_sensor',
    'ip', 'body_material', 'body_material_specified',
    'sku',
]


# ═══════════════════════════════════════════════════════════════
# Section — серии со счётчиками и первым фото (1 быстрый запрос)
# ═══════════════════════════════════════════════════════════════
class LimitSwitchBoxSectionView(APIView):
    """GET /api/pa-controls/sections/"""
    permission_classes = [AllowAny]

    def get(self, request):
        qs = (
            LimitSwitchModelLine.objects
            .filter(limit_switch_box_model_line__is_active=True)
            .annotate(count=Count('limit_switch_box_model_line'))
            .prefetch_related('image_gallery__items__image')
            .select_related('brand')
            .order_by('name')
            .distinct()
        )
        result = []
        for ml in qs:
            img = ml.image_gallery.get_default_image() if ml.image_gallery else None
            result.append({
                'id': ml.id,
                'name': ml.name,
                'code': ml.code or '',
                'count': ml.count,
                'image': (
                    img.preview_file.url if img and img.preview_file
                    else (img.media_file.url if img and img.media_file else None)
                ),
                'brand': {'id': ml.brand.id, 'name': ml.brand.name} if ml.brand else None,
            })
        return Response(result)


# ═══════════════════════════════════════════════════════════════
# Catalog list — карточки товаров (лёгкий to_values_dict)
# ═══════════════════════════════════════════════════════════════
class LimitSwitchBoxCatalogView(APIView):
    """
    GET /api/pa-controls/catalog/

    Параметры: search, model_line_id, sensor_variety_id, points,
               ip_id, work_temp_min/max, body_material_id,
               model_line_brand_id, signal_type_id, exd_id,
               limit / offset
    """
    permission_classes = [AllowAny]

    def get(self, request):
        params = request.query_params

        qs = LimitSwitchBox.objects.select_related(*SELECT_RELATED).prefetch_related(
            'image_gallery__items__image',
            'model_line__image_gallery__items__image',
        )

        is_active = params.get('is_active', 'true')
        if is_active.lower() in ('true', '1'):
            qs = qs.filter(is_active=True)

        filters_applied = {}

        for fd in LimitSwitchBox.FILTER_DEFINITIONS:
            value = params.get(fd.param_name)
            if value is None or value == '' or value == 'all':
                continue
            lookup, converted = fd.build_filter_lookup(value)
            if lookup and converted is not None:
                qs = qs.filter(**{lookup: converted})
                filters_applied[fd.param_name] = value

        search = params.get('search', '').strip()
        if search and SEARCH_FIELDS:
            from django.db.models import Q
            q = Q()
            for field in SEARCH_FIELDS:
                q |= Q(**{f'{field}__icontains': search})
            qs = qs.filter(q)
            filters_applied['search'] = search

        total = qs.count()
        limit = int(params.get('limit', 100))
        offset = int(params.get('offset', 0))
        qs = qs[offset:offset + limit]
        data = [item.to_values_dict() for item in qs]

        return Response({
            'data': data,
            'total': total,
            'filters_applied': filters_applied,
            'limit': limit,
            'offset': offset,
        })


# ═══════════════════════════════════════════════════════════════
# Detail — полная карточка товара (тяжёлый to_dict)
# ═══════════════════════════════════════════════════════════════
class LimitSwitchBoxDetailView(APIView):
    """GET /api/pa-controls/catalog/<id>/"""
    permission_classes = [AllowAny]

    def get(self, request, pk):
        item = get_object_or_404(
            LimitSwitchBox.objects.select_related(*SELECT_RELATED, 'image_gallery', 'model_line__image_gallery').prefetch_related(
                'image_gallery__items__image',
                'tech_docs',
                Prefetch(
                    'additional_sensor',
                    queryset=SensorComponent.objects.select_related(
                        'variety', 'signal_type', 'contact_form', 'contact_state', 'brand',
                    )
                ),
                'model_line__image_gallery__items__image',
                'model_line__tech_docs',
            ),
            pk=pk,
        )
        return Response(item.to_dict())


# ═══════════════════════════════════════════════════════════════
# Filters
# ═══════════════════════════════════════════════════════════════
class LimitSwitchBoxFilterOptionsView(BaseFilterOptionsView):
    """
    GET /api/pa-controls/filters/ — опции для FilterSidebar на фронтенде.

    Наследует get() из BaseFilterOptionsView (core/views.py).
    """
    permission_classes = [AllowAny]
    filter_definitions = LimitSwitchBox.FILTER_DEFINITIONS
    model_class = LimitSwitchBox