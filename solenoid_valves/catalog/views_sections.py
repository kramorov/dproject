# solenoid_valves/catalog/views_sections.py
"""
GET /api/solenoid-valves/sections/ — серии распределительных клапанов со счётчиками и первым фото.

Образец — pa_controls/views/catalog.py (LimitSwitchBoxSectionView): описание серии
локализуется через description_i18n (Accept-Language), имя — торговое, не переводится.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count

from solenoid_valves.models import DirectionalValveModelLine
from core.utils.localization import locale_from_accept_language, pick_i18n


class SolenoidValvesSectionView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        locale = locale_from_accept_language(request.headers.get('Accept-Language'))
        qs = (
            DirectionalValveModelLine.objects
            .filter(direction_valve_model_line__is_active=True)
            .annotate(count=Count('direction_valve_model_line'))
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
