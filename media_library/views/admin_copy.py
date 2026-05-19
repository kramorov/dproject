# media_library/views/admin_copy.py
"""
POST /api/admin/media/<id>/copy/ — создание копии элемента медиабиблиотеки.

Копирует все скалярные атрибуты, НЕ копирует media_file и preview_file.
Название получает суффикс «(копия)».
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny  # TODO: вернуть IsAdminUser

from media_library.models import MediaLibraryItem

logger = logging.getLogger(__name__)


class MediaAdminCopyView(APIView):
    permission_classes = [AllowAny]  # TODO: вернуть IsAdminUser

    def post(self, request, pk):
        logger.info(f"MediaAdminCopyView POST pk={pk}")

        try:
            original = MediaLibraryItem.objects.get(pk=pk)
        except MediaLibraryItem.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        # Поля, которые НЕ копируем
        skip_fields = {'id', 'created_at', 'updated_at', 'media_file', 'preview_file'}

        # Поля, которые сбрасываем
        reset_fields = {'sorting_order', 'is_default'}

        copy_obj = MediaLibraryItem()

        for field in original._meta.fields:
            name = field.name
            if name in skip_fields:
                continue

            value = getattr(original, name)

            if name in reset_fields:
                if isinstance(field, type(original._meta.get_field('sorting_order'))):
                    setattr(copy_obj, name, 0)
                elif isinstance(field, type(original._meta.get_field('is_default'))):
                    setattr(copy_obj, name, False)
                else:
                    setattr(copy_obj, name, None)
            elif name == 'title':
                setattr(copy_obj, name, f"{value or ''} (копия)")
            else:
                setattr(copy_obj, name, value)

        # created_by — текущий пользователь
        if request.user and request.user.is_authenticated:
            copy_obj.created_by = request.user

        copy_obj.save()

        # Копируем M2M-связи (ImageGalleryMixin создаёт M2M на MediaLibraryItem,
        # но с related_name='+', так что они недоступны напрямую — пропускаем)

        logger.info(f"MediaLibraryItem copied: {original.pk} → {copy_obj.pk}")
        return Response(copy_obj.to_dict(), status=status.HTTP_201_CREATED)
