# pneumatic_fittings/catalog/views_sections.py
"""
GET /api/pneumatic-{fittings|silencers|plugs}/sections/ — серии со счётчиками и первым фото.

Три каталога над тремя моделями позиций и тремя моделями серий.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count

from pneumatic_fittings.models import (
    PneumaticFittingModelLine, PneumaticSilencerModelLine, PneumaticPlugModelLine,
)
from core.utils.localization import locale_from_accept_language, pick_i18n


class PneumaticSectionView(APIView):
    permission_classes = [AllowAny]

    model_line_class = None
    item_related_name = ''

    def get(self, request):
        locale = locale_from_accept_language(request.headers.get('Accept-Language'))
        qs = self.model_line_class.objects.filter(
            **{f'{self.item_related_name}__is_active': True},
        )
        qs = (
            qs
            .annotate(count=Count(self.item_related_name))
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
                'description': pick_i18n(
                    getattr(ml, 'description_i18n', None), locale, fallback=ml.description or ''
                ),
                'count': ml.count,
                'image': (
                    img.preview_url if img and img.media_file
                    else (img.media_file.url if img and img.media_file else None)
                ),
                'brand': {'id': ml.brand.id, 'name': ml.brand.name} if ml.brand else None,
            })
        return Response(result)


class PneumaticFittingsSectionView(PneumaticSectionView):
    model_line_class = PneumaticFittingModelLine
    item_related_name = 'pneumaticfitting_items'


class PneumaticSilencersSectionView(PneumaticSectionView):
    model_line_class = PneumaticSilencerModelLine
    item_related_name = 'pneumaticsilencer_items'


class PneumaticPlugsSectionView(PneumaticSectionView):
    model_line_class = PneumaticPlugModelLine
    item_related_name = 'pneumaticplug_items'
