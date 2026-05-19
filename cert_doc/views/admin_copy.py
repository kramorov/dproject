# cert_doc/views/admin_copy.py
"""
POST /api/admin/certs/<id>/copy/ — копия сертификата (CopyMixin).
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from cert_doc.models import CertData

logger = logging.getLogger(__name__)


class CertAdminCopyView(APIView):
    permission_classes = [AllowAny]

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
