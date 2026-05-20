# cert_doc/views/admin_detail.py
"""
PUT  /api/admin/certs/<id>/  — полное обновление сертификата
PATCH  /api/admin/certs/<id>/  — частичное обновление
DELETE /api/admin/certs/<id>/  — физическое удаление

Особенности:
    - PUT требует name и cert_variety_id
    - PATCH обновляет только переданные поля
    - equipment_type_ids (M2M) обновляется через .set()
    - DELETE использует cert.delete(soft=False) — жёсткое удаление
      (обход SoftDeleteMixin.is_deleted)
    - После PUT/PATCH вызывается cert.refresh_from_db()
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


class CertAdminDetailView(APIView):
    permission_classes = [AllowAny]

    def _get(self, pk):
        try:
            return CertData.objects.get(pk=pk)
        except CertData.DoesNotExist:
            return None

    def _resolve_fk(self, model, pk, field_name):
        if pk is None:
            return None, None
        try:
            return model.objects.get(pk=int(pk)), None
        except (model.DoesNotExist, ValueError):
            return None, {'error': f'{field_name} with id={pk} not found'}

    def _update_fields(self, cert, data):
        errors = []
        str_fields = ['name', 'code', 'description', 'issued_by', 'public_url']
        for f in str_fields:
            if f in data:
                setattr(cert, f, data[f].strip() if data[f] else None)

        if 'is_active' in data:
            v = data['is_active']
            cert.is_active = v if isinstance(v, bool) else str(v).lower() in ('true', '1')

        if 'valid_from' in data:
            cert.valid_from = data['valid_from'] or None
        if 'valid_until' in data:
            cert.valid_until = data['valid_until'] or None

        # FK
        for field, model in [
            ('cert_variety_id', CertVariety),
            ('brand_id', Brands),
            ('media_item_id', MediaLibraryItem),
        ]:
            if field in data:
                obj, err = self._resolve_fk(model, data[field], field)
                if err:
                    errors.append(err['error'])
                else:
                    setattr(cert, field.replace('_id', ''), obj)

        return errors

    def _update_m2m(self, cert, data):
        if 'equipment_type_ids' in data:
            et_ids = data['equipment_type_ids']
            if isinstance(et_ids, str):
                et_ids = [x.strip() for x in et_ids.split(',') if x.strip()]
            try:
                et_ids = [int(x) for x in et_ids]
                types = EquipmentType.objects.filter(id__in=et_ids)
                cert.equipment_types.set(types)
            except (ValueError, TypeError):
                pass

    def put(self, request, pk):
        cert = self._get(pk)
        if not cert:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        errors = self._update_fields(cert, request.data)
        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        cert.save()
        self._update_m2m(cert, request.data)
        cert.refresh_from_db()
        return Response(cert.to_dict())

    def patch(self, request, pk):
        cert = self._get(pk)
        if not cert:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        errors = self._update_fields(cert, request.data)
        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        cert.save()
        self._update_m2m(cert, request.data)
        cert.refresh_from_db()
        return Response(cert.to_dict())

    def delete(self, request, pk):
        cert = self._get(pk)
        if not cert:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            cert.delete(soft=False)
            return Response({'success': True})
        except Exception as e:
            logger.error(f"Delete failed for pk={pk}: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
