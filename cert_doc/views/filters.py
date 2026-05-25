# cert_doc/views/filters.py
"""
GET /api/admin/certs/filters/ — опции фильтров для выпадающих списков.

Параметр ?scope=used (по умолчанию) — только значения, для которых есть сертификаты.
Параметр ?scope=all — полные справочники (для формы создания/редактирования).

Возвращает:
    cert_variety_id   — типы сертификатов (из CertVariety)
    brand_id          — бренды (из Brands)
    equipment_type_id — типы оборудования (M2M через CertData.equipment_types)

Каждый элемент: {id, name[, code]}.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from cert_doc.models import CertData, CertVariety
from producers.models import Brands
from core.models import EquipmentType


class CertFilterOptionsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        scope = request.query_params.get('scope', 'used')

        if scope == 'all':
            return self._all_options()
        return self._used_options()

    def _used_options(self):
        """Только значения, для которых есть сертификаты."""
        variety_ids = CertData.objects.values_list('cert_variety_id', flat=True).distinct()
        varieties = list(
            CertVariety.objects.filter(id__in=variety_ids, is_active=True)
            .values('id', 'name', 'code')
        )

        brand_ids = CertData.objects.exclude(brand__isnull=True).values_list('brand_id', flat=True).distinct()
        brands = list(
            Brands.objects.filter(id__in=brand_ids, is_active=True)
            .values('id', 'name')
        )

        eq_ids = CertData.equipment_types.through.objects.values_list('equipmenttype_id', flat=True).distinct()
        equipment_types = list(
            EquipmentType.objects.filter(id__in=eq_ids, is_active=True)
            .values('id', 'name')
        )

        return Response({
            'cert_variety_id': varieties,
            'brand_id': brands,
            'equipment_type_id': equipment_types,
        })

    def _all_options(self):
        """Полные справочники — для формы создания/редактирования."""
        varieties = list(
            CertVariety.objects.filter(is_active=True)
            .values('id', 'name', 'code')
        )
        brands = list(
            Brands.objects.filter(is_active=True)
            .values('id', 'name')
        )
        equipment_types = list(
            EquipmentType.objects.filter(is_active=True)
            .values('id', 'name')
        )
        return Response({
            'cert_variety_id': varieties,
            'brand_id': brands,
            'equipment_type_id': equipment_types,
        })
