# media_library/views/admin_recreate_preview.py
"""
POST — принудительная регенерация вариантов для элемента медиабиблиотеки.

Удаляет старые MediaVariant (файлы из Cloud.ru + строки БД) и создаёт новые.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from project_customers.permissions import SectionAccessPermission  # TODO: вернуть IsAdminUser

from media_library.models import MediaLibraryItem
from media_library.services import delete_variants, generate_variants

logger = logging.getLogger(__name__)


class MediaAdminRecreatePreviewView(APIView):
    permission_classes = [SectionAccessPermission]
    required_section = 'admin_section'  # TODO: вернуть IsAdminUser

    def post(self, request, pk):
        logger.info(f"MediaAdminRecreatePreviewView POST pk={pk}")

        try:
            item = MediaLibraryItem.objects.get(pk=pk)
        except MediaLibraryItem.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        if not item.media_file:
            return Response({'error': 'No media file to generate variants from'},
                            status=status.HTTP_400_BAD_REQUEST)

        if not (item.is_image() or item._is_pdf()):
            return Response({'error': 'Variants only supported for images and PDF'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            delete_variants(item)
            count = generate_variants(item)
            item.refresh_from_db()

            logger.info(f"Variants regenerated for MediaLibraryItem {pk}: {count} created")
            return Response({
                'success': True,
                'message': f'Regenerated {count} variants',
                'variants': item.get_variants_for_api(),
                'item': item.to_dict(),
            })
        except Exception as e:
            logger.error(f"Failed to regenerate variants for {pk}: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
