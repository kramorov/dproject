# media_library/views/admin_upload.py
"""
Загрузка медиафайла — POST multipart/form-data.

Поля:
    name            — str (обязательно)
    code            — str (опционально)
    file            — файл (обязательно, multipart)
    category_id     — int (обязательно, FK → MediaCategory)
    description     — str (опционально)
    equipment_type_id — int (опционально, FK → EquipmentType)
    brand_id        — int (опционально, FK → Brands)
    keywords        — str (опционально, через запятую)
    is_public       — bool (default true)
    is_active       — bool (default true)
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny  # TODO: вернуть IsAdminUser

from media_library.models import MediaLibraryItem, MediaCategory
from core.models import EquipmentType
from producers.models import Brands

logger = logging.getLogger(__name__)


class MediaAdminUploadView(APIView):
    permission_classes = [AllowAny]  # TODO: вернуть IsAdminUser

    def post(self, request):
        logger.info("MediaAdminUploadView POST")

        # --- Валидация обязательных полей ---
        name = request.data.get('name', '').strip()
        if not name:
            return Response({'error': 'name is required'}, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({'error': 'file is required'}, status=status.HTTP_400_BAD_REQUEST)

        if uploaded_file.size > 100 * 1024 * 1024:
            return Response({'error': 'file size exceeds 100 MB'}, status=status.HTTP_400_BAD_REQUEST)

        category_id = request.data.get('category_id')
        if not category_id:
            return Response({'error': 'category_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        # --- FK-резолвинг ---
        try:
            category = MediaCategory.objects.get(pk=int(category_id))
        except (MediaCategory.DoesNotExist, ValueError):
            return Response({'error': f'MediaCategory with id={category_id} not found'},
                            status=status.HTTP_400_BAD_REQUEST)

        equipment_type = None
        et_id = request.data.get('equipment_type_id')
        if et_id:
            try:
                equipment_type = EquipmentType.objects.get(pk=int(et_id))
            except (EquipmentType.DoesNotExist, ValueError):
                return Response({'error': f'EquipmentType with id={et_id} not found'},
                                status=status.HTTP_400_BAD_REQUEST)

        brand = None
        brand_id = request.data.get('brand_id')
        if brand_id:
            try:
                brand = Brands.objects.get(pk=int(brand_id))
            except (Brands.DoesNotExist, ValueError):
                return Response({'error': f'Brands with id={brand_id} not found'},
                                status=status.HTTP_400_BAD_REQUEST)

        # --- Создание ---
        try:
            item = MediaLibraryItem(
                name=name,
                code=request.data.get('code', ''),
                description=request.data.get('description', ''),
                media_file=uploaded_file,
                category=category,
                equipment_type=equipment_type,
                brand=brand,
                keywords=request.data.get('keywords', ''),
                is_public=request.data.get('is_public', 'true') in ('true', 'True', '1', True),
                is_active=request.data.get('is_active', 'true') in ('true', 'True', '1', True),
                created_by=request.user if request.user.is_authenticated else None,
            )
            item.save()  # save() автоопределяет mime_type и создаёт preview

            logger.info(f"MediaLibraryItem created: id={item.pk}, name={item.name}")
            return Response(item.to_dict(), status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating MediaLibraryItem: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
