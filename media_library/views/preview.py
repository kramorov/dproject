# media_library/views/preview.py
"""
GET — просмотр превью или файла в браузере.

Для изображений отдаёт preview_file (если есть), иначе оригинал.
Для PDF отдаёт как inline.
Для остальных — скачивание (как download).
"""
import logging
from django.http import Http404, FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from media_library.models import MediaLibraryItem

logger = logging.getLogger(__name__)


class MediaPreviewView(APIView):
    permission_classes = [AllowAny]

    # MIME-типы, которые безопасно показывать inline
    SAFE_INLINE_TYPES = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml',
        'application/pdf',
        'text/plain', 'text/html', 'text/css',
        'audio/mpeg', 'audio/wav', 'audio/ogg',
        'video/mp4', 'video/webm', 'video/ogg',
    }

    def get(self, request, pk):
        logger.info(f"MediaPreviewView GET pk={pk}")

        try:
            item = MediaLibraryItem.objects.get(pk=pk)
        except MediaLibraryItem.DoesNotExist:
            raise Http404("Media file not found")

        if not item.is_active and not request.user.is_staff:
            raise Http404("Media file not found")

        if not item.is_public and not request.user.is_authenticated:
            return Response(
                {'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN
            )

        # Выбираем, что отдавать: превью или оригинал
        file_field = None
        content_type = item.mime_type or 'application/octet-stream'

        if item.is_image() and item.preview_file and item.preview_file.name:
            if item.preview_file.storage.exists(item.preview_file.name):
                file_field = item.preview_file
                content_type = 'image/jpeg'  # preview всегда JPEG

        if file_field is None:
            if not item.media_file or not item.media_file.name:
                raise Http404("File not found")
            if not item.media_file.storage.exists(item.media_file.name):
                raise Http404("File not found on storage")
            file_field = item.media_file

        # Определяем Content-Disposition
        is_safe = content_type in self.SAFE_INLINE_TYPES or item.is_image()
        disposition = 'inline' if is_safe else 'attachment'

        response = FileResponse(
            file_field.open('rb'),
            content_type=content_type,
            as_attachment=(disposition == 'attachment'),
            filename=item.filename,
        )
        response['Content-Disposition'] = f'{disposition}; filename="{item.filename}"'
        response['Content-Length'] = file_field.size
        response['X-Content-Type-Options'] = 'nosniff'

        logger.info(f"Preview: {item.filename} (id={pk}, inline={is_safe})")
        return response
