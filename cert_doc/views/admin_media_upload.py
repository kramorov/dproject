# cert_doc/views/admin_media_upload.py
"""
POST /api/admin/certs/upload-media/ — загрузка файла сертификата в медиатеку.

Создаёт MediaLibraryItem и возвращает его id.
Поля медиафайла автозаполняются из параметров сертификата.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from media_library.models import MediaLibraryItem, MediaCategory
from core.models import EquipmentType
from producers.models import Brands

logger = logging.getLogger(__name__)


class CertMediaUploadView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({'error': 'file is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Авто-категория: CERTIFICATE
        try:
            category = MediaCategory.objects.get(code='CERTIFICATE')
        except MediaCategory.DoesNotExist:
            return Response({'error': 'MediaCategory CERTIFICATE not found'}, status=status.HTTP_400_BAD_REQUEST)

        # Из параметров сертификата
        title = request.data.get('title', '').strip() or uploaded_file.name
        equipment_type = None
        brand = None

        et_id = request.data.get('equipment_type_id')
        if et_id:
            try:
                equipment_type = EquipmentType.objects.get(pk=int(et_id))
            except EquipmentType.DoesNotExist:
                pass

        b_id = request.data.get('brand_id')
        if b_id:
            try:
                brand = Brands.objects.get(pk=int(b_id))
            except Brands.DoesNotExist:
                pass

        item = MediaLibraryItem(
            title=title,
            category=category,
            equipment_type=equipment_type,
            brand=brand,
            media_file=uploaded_file,
            is_public=True,
            created_by=request.user if request.user.is_authenticated else None,
        )
        item.save()

        return Response({'id': item.id, 'title': item.title, **item.to_dict()}, status=status.HTTP_201_CREATED)
