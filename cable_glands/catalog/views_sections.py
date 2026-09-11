# cable_glands/catalog/views_sections.py
"""
GET /api/cable-glands/sections/ — серии кабельных вводов со счётчиками и первым фото.

Отдельный эндпоинт нужен, потому что CatalogSection на фронте без него делает
fallback на `list({limit: 1000})`, а список серверно режется до 200 записей —
при 972 артикулах это теряло бы часть серий.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count

from cable_glands.models import CableGlandModelLine


class CableGlandSectionView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = (
            CableGlandModelLine.objects
            .filter(cable_gland_articles__is_active=True)
            .annotate(count=Count('cable_gland_articles'))
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
                'description': ml.description or '',
                'count': ml.count,
                'image': img.get_serve_url() if img else None,
                'brand': {'id': ml.brand.id, 'name': ml.brand.name} if ml.brand else None,
            })
        return Response(result)
