# media_library/views/admin_copy.py
"""
POST /api/admin/media/<id>/copy/ — создание копии элемента медиабиблиотеки.

Вся логика копирования — в MediaLibraryItem.copy().
Название получает суффикс «(копия)», файлы не копируются.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from project_customers.permissions import SectionAccessPermission

from media_library.models import MediaLibraryItem

logger = logging.getLogger(__name__)


class MediaAdminCopyView(APIView):
    permission_classes = [SectionAccessPermission]
    required_section = 'admin_section'

    def post(self, request, pk):
        logger.info(f"MediaAdminCopyView POST pk={pk}")

        try:
            original = MediaLibraryItem.objects.get(pk=pk)
        except MediaLibraryItem.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user if request.user.is_authenticated else None
        copy_obj = original.copy(created_by=user)

        logger.info(f"MediaLibraryItem copied: {original.pk} -> {copy_obj.pk}")
        return Response(copy_obj.to_dict(), status=status.HTTP_201_CREATED)
