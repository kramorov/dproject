# media_library/views/filters.py
"""
GET /api/admin/media/filters/ — опции фильтров для выпадающих списков.

Параметр ?scope=used (по умолчанию) — только значения, для которых есть медиафайлы.
Параметр ?scope=all — полные справочники (для формы создания/редактирования).

Возвращает:
    category_id        — категории (из MediaCategory)
    equipment_type_id  — типы оборудования (из EquipmentType)
    brand_id           — бренды (из Brands)

Каждый элемент: {id, name[, code, icon]}.

Состав фильтров определяется здесь, а не в модели.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from media_library.models import MediaLibraryItem, MediaCategory
from core.models import EquipmentType
from producers.models import Brands


class MediaFilterOptionsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        scope = request.query_params.get('scope', 'used')

        if scope == 'all':
            return self._all_options()
        return self._used_options()

    def _used_options(self):
        """Только значения, для которых есть записи в медиатеке."""
        cat_ids = MediaLibraryItem.objects.values_list('category_id', flat=True).distinct()
        categories = list(
            MediaCategory.objects.filter(id__in=cat_ids, is_active=True)
            .values('id', 'name', 'code', 'icon')
        )

        # Только типы оборудования с файлами
        et_ids = MediaLibraryItem.objects.exclude(
            equipment_type__isnull=True
        ).values_list('equipment_type_id', flat=True).distinct()
        equipment_types = list(
            EquipmentType.objects.filter(id__in=et_ids, is_active=True)
            .values('id', 'name')
        )

        # Только бренды с файлами
        brand_ids = MediaLibraryItem.objects.exclude(
            brand__isnull=True
        ).values_list('brand_id', flat=True).distinct()
        brands = list(
            Brands.objects.filter(id__in=brand_ids, is_active=True)
            .values('id', 'name')
        )

        return Response({
            'category_id': categories,
            'equipment_type_id': equipment_types,
            'brand_id': brands,
        })

    def _all_options(self):
        """Полные справочники — для формы создания/редактирования."""
        categories = list(
            MediaCategory.objects.filter(is_active=True)
            .values('id', 'name', 'code', 'icon')
        )
        equipment_types = list(
            EquipmentType.objects.filter(is_active=True)
            .values('id', 'name')
        )
        brands = list(
            Brands.objects.filter(is_active=True)
            .values('id', 'name')
        )
        return Response({
            'category_id': categories,
            'equipment_type_id': equipment_types,
            'brand_id': brands,
        })
