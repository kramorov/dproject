# media_library/views/admin_variants.py
"""
GET — получить варианты элемента без регенерации.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from media_library.models import MediaLibraryItem

logger = logging.getLogger(__name__)


class MediaAdminVariantsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            item = MediaLibraryItem.objects.get(pk=pk)
        except MediaLibraryItem.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'variants': item.get_variants_for_api(),
        })
