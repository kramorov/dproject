# cert_doc/views/filters.py
"""
GET /api/admin/certs/filters/ — опции фильтров для выпадающих списков.

Возвращает только те значения, для которых есть сертификаты:
    cert_variety_id   — типы сертификатов (из CertVariety)
    brand_id          — бренды (из Brands)
    equipment_type_id — типы оборудования (M2M через CertData.equipment_types)

Каждый элемент: {id, name[, code]}.

Состав фильтров определяется здесь, а не в модели.
Чтобы добавить/убрать фильтр — меняйте этот view,
модель CertData.FILTER_DEFINITIONS не трогайте.
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
        # Только типы сертификатов, используемые в CertData
        variety_ids = CertData.objects.values_list('cert_variety_id', flat=True).distinct()
        varieties = list(
            CertVariety.objects.filter(id__in=variety_ids, is_active=True)
            .values('id', 'name', 'code')
        )

        # Только бренды, используемые в CertData
        brand_ids = CertData.objects.exclude(brand__isnull=True).values_list('brand_id', flat=True).distinct()
        brands = list(
            Brands.objects.filter(id__in=brand_ids, is_active=True)
            .values('id', 'name')
        )

        # Только типы оборудования, связанные с сертификатами через M2M
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
