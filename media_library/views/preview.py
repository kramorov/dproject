# media_library/views/preview.py
"""
GET — просмотр превью или файла в браузере.

Для изображений отдаёт preview_file (если есть), иначе оригинал.
Для PDF отдаёт как inline.

Режим зависит от settings.MEDIA_SERVE_MODE:
    'proxy'    — Django читает файл и стримит клиенту
    'redirect' — редирект на presigned URL (клиент качает напрямую из S3)
"""
import logging
from django.http import Http404, FileResponse, HttpResponseRedirect
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from media_library.models import MediaLibraryItem

logger = logging.getLogger(__name__)


class MediaPreviewView(APIView):
    permission_classes = [AllowAny]

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

        try:
            if not item.is_public and not request.user.is_authenticated:
                return Response(
                    {'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN
                )

            mode = getattr(settings, 'MEDIA_SERVE_MODE', 'redirect')

            # Выбираем файл: превью или оригинал
            file_field = None
            content_type = item.mime_type or 'application/octet-stream'
            is_previewable = item.is_image() or item.file_extension.lower() == 'pdf'

            if is_previewable and item.preview_file and item.preview_file.name:
                if item.preview_file.storage.exists(item.preview_file.name):
                    file_field = item.preview_file
                    content_type = 'image/jpeg'

            if file_field is None:
                if not item.media_file or not item.media_file.name:
                    raise Http404("File not found")
                if not item.media_file.storage.exists(item.media_file.name):
                    raise Http404("File not found on storage")
                file_field = item.media_file

            if mode == 'redirect':
                url = file_field.url
                return HttpResponseRedirect(url)
            if mode == 'direct':
                url = item.public_url or file_field.url
                return HttpResponseRedirect(url)

            # proxy mode — стримим через Django
            is_safe = content_type in self.SAFE_INLINE_TYPES or is_previewable
            disposition = 'inline' if is_safe else 'attachment'

            try:
                f = file_field.open('rb')
            except Exception as e:
                logger.error(f"Preview open failed pk={pk}: {e}")
                raise Http404("File not accessible")

            response = FileResponse(
                f,
                content_type=content_type,
                as_attachment=(disposition == 'attachment'),
                filename=item.filename,
            )
            response['Content-Disposition'] = f'{disposition}; filename="{item.filename}"'
            response['Content-Length'] = file_field.size
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'SAMEORIGIN'

            logger.info(f"Preview proxy: {item.filename} (id={pk}, inline={is_safe})")
            return response
        except Http404:
            raise
        except Exception as e:
            logger.error(f"Preview unhandled error pk={pk}: {e}", exc_info=True)
            raise Http404("Error loading preview")