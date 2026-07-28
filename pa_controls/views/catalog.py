# pa_controls/views/catalog.py
"""
API каталога блоков концевых выключателей — SectionView.

CatalogView, DetailView, FilterOptionsView перенесены в pa_controls/catalog/.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count

from pa_controls.models.lsb_model_line import LimitSwitchModelLine


class LimitSwitchBoxSectionView(APIView):
    """GET /api/pa-controls/sections/ — серии со счётчиками и первым фото."""
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
                'description': ml.description or '',
                'count': ml.count,
                'image': (
                    img.preview_url if img and img.media_file
                    else (img.media_file.url if img and img.media_file else None)
                ),
                'brand': {'id': ml.brand.id, 'name': ml.brand.name} if ml.brand else None,
            })
        return Response(result)