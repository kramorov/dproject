# pneumatic_fittings/catalog/views_sections.py
"""
GET /api/pneumatic-{fittings|silencers|plugs}/sections/ — серии со счётчиками и первым фото.

Три каталога над одной моделью PneumaticFitting (вид = equipment_type.code серии):
  fitting-thread-pipe / fitting-silencer / fitting-plug.

Образец — pa_controls/views/catalog.py (LimitSwitchBoxSectionView): описание серии
локализуется через description_i18n (Accept-Language), имя — торговое, не переводится.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count

from pneumatic_fittings.models import PneumaticFittingModelLine
from core.utils.localization import locale_from_accept_language, pick_i18n


class PneumaticSectionView(APIView):
    permission_classes = [AllowAny]

    # код вида (equipment_type серии); '' — все виды
    kind_code = ''

    def get(self, request):
        locale = locale_from_accept_language(request.headers.get('Accept-Language'))
        qs = PneumaticFittingModelLine.objects.filter(
            pneumatic_fitting_model_line_new__is_active=True,
        )
        if self.kind_code:
            qs = qs.filter(pneumatic_fitting_model_line_new__equipment_type__code=self.kind_code)
        qs = (
            qs
            .annotate(count=Count('pneumatic_fitting_model_line_new'))
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
    kind_code = 'fitting-thread-pipe'


class PneumaticSilencersSectionView(PneumaticSectionView):
    kind_code = 'fitting-silencer'


class PneumaticPlugsSectionView(PneumaticSectionView):
    kind_code = 'fitting-plug'
