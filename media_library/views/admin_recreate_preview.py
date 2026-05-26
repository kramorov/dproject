# media_library/views/admin_recreate_preview.py
"""
POST — принудительное пересоздание превью для элемента медиабиблиотеки.

Вызывает MediaLibraryItem.recreate_preview():
    - удаляет старое превью (если есть)
    - создаёт новое (JPEG для изображений, первая страница для PDF)
    - сохраняет preview_file в БД

Возвращает to_dict() с обновлённым preview-полем.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny  # TODO: вернуть IsAdminUser

from media_library.models import MediaLibraryItem

logger = logging.getLogger(__name__)


class MediaAdminRecreatePreviewView(APIView):
    permission_classes = [AllowAny]  # TODO: вернуть IsAdminUser

    def post(self, request, pk):
        logger.info(f"MediaAdminRecreatePreviewView POST pk={pk}")

        try:
            item = MediaLibraryItem.objects.get(pk=pk)
        except MediaLibraryItem.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        if not item.media_file:
            return Response({'error': 'No media file to create preview from'},
                            status=status.HTTP_400_BAD_REQUEST)

        success, message = item.recreate_preview()
        item.refresh_from_db()

        if success:
            logger.info(f"Preview recreated for MediaLibraryItem {pk}")
            return Response({
                'success': True,
                'message': message,
                'item': item.to_dict(),
            })
        else:
            logger.warning(f"Failed to recreate preview for MediaLibraryItem {pk}: {message}")
            return Response({
                'success': False,
                'message': message,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
