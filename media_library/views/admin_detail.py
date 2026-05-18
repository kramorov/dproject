# media_library/views/admin_detail.py
"""
PUT / PATCH / DELETE — редактирование и удаление элемента медиабиблиотеки.

PUT  — полное обновление (включая замену файла, если передан file)
PATCH — частичное обновление
DELETE — удаление с очисткой файлов на диске
"""
import logging
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser

from media_library.models import MediaLibraryItem, MediaCategory
from core.models import EquipmentType
from producers.models import Brands
from storage_manager.services import file_service

logger = logging.getLogger(__name__)


class MediaAdminDetailView(APIView):
    permission_classes = [IsAdminUser]

    def _get_item(self, pk):
        """Получить объект или 404."""
        try:
            return MediaLibraryItem.objects.get(pk=pk)
        except MediaLibraryItem.DoesNotExist:
            return None

    def _resolve_fk(self, model, pk, field_name):
        """Резолв FK — возвращает объект или ошибку."""
        if pk is None:
            return None, None
        try:
            return model.objects.get(pk=int(pk)), None
        except (model.DoesNotExist, ValueError):
            return None, {'error': f'{field_name} with id={pk} not found'}

    def _update_scalar_fields(self, item, data):
        """Обновляет скалярные поля из request.data. Возвращает список ошибок."""
        errors = []

        # Текстовые поля
        for field in ('title', 'description', 'keywords'):
            if field in data:
                setattr(item, field, data[field])

        # Булевы поля
        for field in ('is_public', 'is_active'):
            if field in data:
                val = data[field]
                if isinstance(val, str):
                    val = val.lower() in ('true', '1', 'yes')
                setattr(item, field, bool(val))

        # Числовые поля
        if 'sorting_order' in data:
            try:
                item.sorting_order = int(data['sorting_order'])
            except (ValueError, TypeError):
                errors.append('sorting_order must be an integer')

        if 'is_default' in data:
            val = data['is_default']
            if isinstance(val, str):
                val = val.lower() in ('true', '1', 'yes')
            item.is_default = bool(val)

        # FK-поля
        for field_name, model_class in (
            ('category_id', MediaCategory),
            ('equipment_type_id', EquipmentType),
            ('brand_id', Brands),
        ):
            if field_name in data:
                obj, err = self._resolve_fk(model_class, data[field_name], field_name)
                if err:
                    errors.append(err['error'])
                else:
                    setattr(item, field_name.replace('_id', ''), obj)

        return errors

    # ── PUT ──────────────────────────────────────────────
    def put(self, request, pk):
        logger.info(f"MediaAdminDetailView PUT pk={pk}")

        item = self._get_item(pk)
        if item is None:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        # Проверка обязательных полей для PUT
        if not request.data.get('title', '').strip():
            return Response({'error': 'title is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not request.data.get('category_id'):
            return Response({'error': 'category_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Замена файла (опционально)
        new_file = request.FILES.get('file')
        if new_file:
            if new_file.size > 100 * 1024 * 1024:
                return Response({'error': 'file size exceeds 100 MB'}, status=status.HTTP_400_BAD_REQUEST)
            # Удаляем старые файлы
            old_media_path = item.media_file.name if item.media_file else None
            old_preview_path = item.preview_file.name if item.preview_file else None
            item.media_file = new_file
            item.mime_type = None  # автоопределится в save()
            if old_media_path:
                file_service.delete_file(old_media_path)
            if old_preview_path:
                file_service.delete_file(old_preview_path)

        # Обновление полей
        errors = self._update_scalar_fields(item, request.data)
        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item.save()  # автоопределит MIME и создаст preview
            logger.info(f"MediaLibraryItem updated: id={item.pk}")
            return Response(item.to_dict())
        except Exception as e:
            logger.error(f"Error updating MediaLibraryItem {pk}: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ── PATCH ────────────────────────────────────────────
    def patch(self, request, pk):
        logger.info(f"MediaAdminDetailView PATCH pk={pk}")

        item = self._get_item(pk)
        if item is None:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        # Замена файла (опционально)
        new_file = request.FILES.get('file')
        if new_file:
            if new_file.size > 100 * 1024 * 1024:
                return Response({'error': 'file size exceeds 100 MB'}, status=status.HTTP_400_BAD_REQUEST)
            old_media_path = item.media_file.name if item.media_file else None
            old_preview_path = item.preview_file.name if item.preview_file else None
            item.media_file = new_file
            item.mime_type = None
            if old_media_path:
                file_service.delete_file(old_media_path)
            if old_preview_path:
                file_service.delete_file(old_preview_path)

        # Частичное обновление полей
        errors = self._update_scalar_fields(item, request.data)
        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item.save()
            logger.info(f"MediaLibraryItem patched: id={item.pk}")
            return Response(item.to_dict())
        except Exception as e:
            logger.error(f"Error patching MediaLibraryItem {pk}: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ── DELETE ───────────────────────────────────────────
    def delete(self, request, pk):
        logger.info(f"MediaAdminDetailView DELETE pk={pk}")

        item = self._get_item(pk)
        if item is None:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            # 1. Очищаем физические файлы
            if item.media_file:
                file_service.delete_file(item.media_file.name)
            if item.preview_file:
                file_service.delete_file(item.preview_file.name)

            # 2. Очищаем M2M-связи через Django ORM
            #    ImageGalleryMixin создаёт M2M на MediaLibraryItem,
            #    чистим явно, чтобы избежать каскадного бага.
            for rel in item._meta.related_objects:
                if rel.many_to_many:
                    getattr(item, rel.get_accessor_name()).clear()

            # 3. Обнуляем FK (CertData.media_item) сырым SQL
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE cert_doc_certdata SET media_item_id = NULL WHERE media_item_id = %s",
                    [item.pk],
                )

            # 4. Удаляем запись сырым SQL (обход бага каскадного коллектора Django)
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM media_library_medialibraryitem WHERE id = %s",
                    [item.pk],
                )

            logger.info(f"MediaLibraryItem deleted: id={pk}")
            return Response({'success': True}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error deleting MediaLibraryItem {pk}: {str(e)}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
