# cert_doc/views/admin_create.py
"""
POST /api/admin/certs/ — создание сертификата.

Поля:
    name, code, description, cert_variety_id, brand_id, equipment_type_ids,
    issued_by, valid_from, valid_until, public_url, media_item_id, is_active
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny  # TODO: IsAdminUser

from cert_doc.models import CertData, CertVariety
from producers.models import Brands
from media_library.models import MediaLibraryItem
from core.models import EquipmentType

logger = logging.getLogger(__name__)


class CertAdminCreateView(APIView):
    permission_classes = [AllowAny]

    def _resolve_fk(self, model, pk, field_name):
        if pk is None:
            return None, None
        try:
            return model.objects.get(pk=int(pk)), None
        except (model.DoesNotExist, ValueError):
            return None, {'error': f'{field_name} with id={pk} not found'}

    def post(self, request):
        logger.info("CertAdminCreateView POST")

        data = request.data
        errors = []

        # Обязательные поля
        name = data.get('name', '').strip()
        if not name:
            errors.append('name is required')

        cert_variety_id = data.get('cert_variety_id')
        if not cert_variety_id:
            errors.append('cert_variety_id is required')

        # FK-резолвинг
        cert_variety, err = self._resolve_fk(CertVariety, cert_variety_id, 'cert_variety')
        if err: errors.append(err['error'])

        brand, err = self._resolve_fk(Brands, data.get('brand_id'), 'brand')
        if err: errors.append(err['error'])

        media_item, err = self._resolve_fk(MediaLibraryItem, data.get('media_item_id'), 'media_item')
        if err: errors.append(err['error'])

        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        # Даты
        valid_from = data.get('valid_from') or None
        valid_until = data.get('valid_until') or None

        # Создание
        cert = CertData(
            name=name,
            code=data.get('code', '').strip() or None,
            description=data.get('description', '').strip() or None,
            cert_variety=cert_variety,
            brand=brand,
            media_item=media_item,
            issued_by=data.get('issued_by', '').strip() or None,
            valid_from=valid_from,
            valid_until=valid_until,
            public_url=data.get('public_url', '').strip() or None,
            is_active=data.get('is_active', True) in (True, 'true', 'True', '1'),
        )
        cert.save()

        # M2M equipment_types
        et_ids = data.get('equipment_type_ids', [])
        if et_ids:
            if isinstance(et_ids, str):
                et_ids = [x.strip() for x in et_ids.split(',') if x.strip()]
            try:
                et_ids = [int(x) for x in et_ids]
                types = EquipmentType.objects.filter(id__in=et_ids)
                cert.equipment_types.set(types)
            except (ValueError, TypeError):
                pass

        logger.info(f"CertData created: id={cert.pk}")
        return Response(cert.to_dict(), status=status.HTTP_201_CREATED)
