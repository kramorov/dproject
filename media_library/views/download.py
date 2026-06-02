# media_library/views/download.py
"""
GET — скачивание медиафайла или варианта.

Параметры:
    ?variant=email — отдать email-вариант (сжатый PDF) вместо оригинала.

Отдаёт файл как бинарный поток с правильными заголовками:
- Content-Type из mime_type
- Content-Disposition: attachment
- Content-Length
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

        variant = request.GET.get('variant', '')
        mode = getattr(settings, 'MEDIA_SERVE_MODE', 'redirect')
        custom_filename = request.GET.get('filename', '')

        # ── Имя файла для скачивания: query-параметр → item.name → item.filename ──
        ext = item.file_extension or ''
        download_name = custom_filename or (f"{item.name or 'document'}.{ext}" if ext else (item.name or 'document'))

        if variant == 'email':
            v = item.variants.filter(role='email').first()
            if not v:
                raise Http404("Email variant not found")
            # Стримим напрямую — редирект ломает Content-Disposition
            from storage_manager.services import file_service
            try:
                f = file_service.storage.open(v.file_path, 'rb')
            except Exception:
                raise Http404("Variant file not accessible")
            content_type = f'image/{v.format}' if v.format != 'pdf' else 'application/pdf'
            response = FileResponse(f, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{download_name}"'
            response['Content-Length'] = v.file_size
            return response

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
            filename=download_name,
        )
        response['Content-Length'] = item.media_file.size
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'SAMEORIGIN'

        logger.info(f"Download: {item.filename} (id={pk})")
        return response
