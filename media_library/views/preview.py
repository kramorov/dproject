# media_library/views/preview.py
"""
GET — просмотр превью или файла в браузере.

Для изображений/PDF отдаёт подходящий вариант из MediaVariant (card/thumb),
фолбэк — preview_file, затем оригинал.

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
from storage_manager.services import file_service

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

            force_proxy = request.GET.get('proxy') == '1'
            mode = 'proxy' if force_proxy else getattr(settings, 'MEDIA_SERVE_MODE', 'redirect')
            is_previewable = item.is_image() or item.file_extension.lower() == 'pdf'

            # Определяем URL для отдачи
            serve_url = None
            content_type = item.mime_type or 'application/octet-stream'

            if is_previewable:
                # Пробуем MediaVariant: card(400) → thumb(150) → icon(50)
                for role in ('card', 'thumb', 'icon'):
                    v = item.variants.filter(role=role).order_by('width').first()
                    if v:
                        serve_url = file_service.get_file_url(v.file_path)
                        content_type = f'image/{v.format}' if v.format != 'pdf' else 'application/pdf'
                        break

                # Фолбэк: старый preview_file
                if not serve_url and item.preview_file and item.preview_file.name:
                    if item.preview_file.storage.exists(item.preview_file.name):
                        if mode == 'redirect':
                            serve_url = item.preview_file.url
                        else:
                            serve_url = None  # будем стримить ниже
                        content_type = 'image/jpeg'

            # Фолбэк: оригинал
            if not serve_url:
                if not item.media_file or not item.media_file.name:
                    raise Http404("File not found")
                if not item.media_file.storage.exists(item.media_file.name):
                    raise Http404("File not found on storage")
                if mode == 'redirect':
                    serve_url = item.media_file.url
                # для proxy mode serve_url остаётся None — стримим ниже

            if mode == 'redirect' and serve_url:
                return HttpResponseRedirect(serve_url)
            if mode == 'direct':
                url = item.public_url or serve_url
                if url:
                    return HttpResponseRedirect(url)

            # proxy mode — стримим через Django
            is_safe = content_type in self.SAFE_INLINE_TYPES or is_previewable
            disposition = 'inline' if is_safe else 'attachment'

            try:
                f = item.media_file.open('rb')
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
            response['Content-Length'] = item.media_file.size
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'SAMEORIGIN'
            response['Access-Control-Allow-Origin'] = '*'

            logger.info(f"Preview proxy: {item.filename} (id={pk}, inline={is_safe})")
            return response
        except Http404:
            raise
        except Exception as e:
            logger.error(f"Preview unhandled error pk={pk}: {e}", exc_info=True)
            raise Http404("Error loading preview")
