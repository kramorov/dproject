# media_library/views/admin_regenerate_variants.py
"""
POST — генерация вариантов из загруженного файла без замены media_file.

Принимает multipart/form-data с полем 'file'.
Генерирует MediaVariant из переданного файла, оригинальный media_file не трогает.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny  # TODO: вернуть IsAdminUser

from media_library.models import MediaLibraryItem
from media_library.services import delete_variants, generate_variants

logger = logging.getLogger(__name__)


class MediaAdminRegenerateVariantsView(APIView):
    permission_classes = [AllowAny]  # TODO: вернуть IsAdminUser

    def post(self, request, pk):
        logger.info(f"MediaAdminRegenerateVariantsView POST pk={pk}")

        try:
            item = MediaLibraryItem.objects.get(pk=pk)
        except MediaLibraryItem.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'error': 'file is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not (item.is_image() or item._is_pdf()):
            return Response({'error': 'Variants only supported for images and PDF'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            delete_variants(item)
            count = generate_variants(item, source_file=uploaded)
            item.refresh_from_db()

            logger.info(f"Variants regenerated from external file for {pk}: {count}")
            return Response({
                'success': True,
                'message': f'Сгенерировано {count} вариантов',
                'item': item.to_dict(),
            })
        except Exception as e:
            logger.error(f"Failed to regenerate variants for {pk}: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
