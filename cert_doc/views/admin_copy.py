# cert_doc/views/admin_copy.py
"""
POST /api/admin/certs/<id>/copy/ — создание копии сертификата.

Использует CertData.copy() (CopyMixin):
    - Копирует все скалярные поля + M2M equipment_types
    - code и name получают суффикс « (копия)»
    - media_item сбрасывается в None
    - sorting_order сбрасывается в 0

Возвращает:
    201 — new_cert.to_dict()
    404 — оригинал не найден
    500 — ошибка копирования с текстом исключения
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from project_customers.permissions import SectionAccessPermission

from cert_doc.models import CertData

logger = logging.getLogger(__name__)


class CertAdminCopyView(APIView):
    permission_classes = [SectionAccessPermission]
    required_section = 'admin_section'

    def post(self, request, pk):
        try:
            original = CertData.objects.get(pk=pk)
        except CertData.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            new_cert = original.copy()
            logger.info(f"CertData copied: {original.pk} → {new_cert.pk}")
            return Response(new_cert.to_dict(), status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Copy failed for pk={pk}: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
