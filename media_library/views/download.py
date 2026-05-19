# media_library/views/download.py
"""
GET — скачивание медиафайла.

Отдаёт файл как бинарный поток с правильными заголовками:
- Content-Type из mime_type
- Content-Disposition: attachment
- Content-Length
"""
import logging
from django.http import Http404, FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from media_library.models import MediaLibraryItem

logger = logging.getLogger(__name__)


class MediaDownloadView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        logger.info(f"MediaDownloadView GET pk={pk}")

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

        if not item.media_file or not item.media_file.name:
            raise Http404("File not found")

        if not item.media_file.storage.exists(item.media_file.name):
            raise Http404("File not found on storage")

        inline_types = {'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf'}
        as_attachment = item.mime_type not in inline_types

        response = FileResponse(
            item.media_file.open('rb'),
            content_type=item.mime_type or 'application/octet-stream',
            as_attachment=as_attachment,
            filename=item.filename,
        )
        response['Content-Length'] = item.media_file.size
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'SAMEORIGIN'

        logger.info(f"Download: {item.filename} (id={pk})")
        return response
