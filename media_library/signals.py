import logging
from django.db.models.signals import post_save , pre_delete , post_migrate
from django.dispatch import receiver
from django.conf import settings
from .models import MediaLibraryItem , MediaCategory

logger = logging.getLogger(__name__)


@receiver(post_migrate)
def create_predefined_categories(sender , **kwargs) :
    """Создает предопределенные категории после миграций"""
    if sender.name == 'media_library' :
        logger.info("Проверка предопределенных категорий медиабиблиотеки")
        try :
            MediaCategory.get_or_create_predefined()
            logger.info("Предопределенные категории медиабиблиотеки созданы/проверены")
        except Exception as e :
            logger.error(f"Ошибка при создании предопределенных категорий: {str(e)}")


@receiver(pre_delete , sender=MediaLibraryItem)
def cleanup_media_files(sender , instance , **kwargs) :
    """Очистка файлов перед удалением объекта"""
    logger.info(f"Удаление файлов для медиа-элемента {instance.pk}")

    try :
        from storage_manager.services import file_service

        # Удаляем основной файл
        if instance.media_file and instance.media_file.name :
            if file_service.file_exists(instance.media_file.name) :
                file_service.delete_file(instance.media_file.name)
                logger.info(f"Удален медиа-файл: {instance.media_file.name}")

        # Удаляем превью
        if instance.preview_file and instance.preview_file.name :
            if file_service.file_exists(instance.preview_file.name) :
                file_service.delete_file(instance.preview_file.name)
                logger.info(f"Удалено превью: {instance.preview_file.name}")

    except Exception as e :
        logger.error(f"Ошибка при удалении файлов медиа-элемента {instance.pk}: {str(e)}")


@receiver(post_save , sender=MediaLibraryItem)
def create_preview_on_save(sender , instance , created , **kwargs) :
    """Создает превью после сохранения если его нет"""
    # ЭТОТ СИГНАЛ МОЖЕТ КОНФЛИКТОВАТЬ - можно закомментировать
    # если превью создается в модели.save()
    # if instance.is_image() and instance.media_file and not instance.preview_file :
    #     logger.info(f"Создание превью для медиа-элемента {instance.pk}")
    #     try :
    #         # Убираем time.sleep - это плохая практика
    #         # Вместо этого используем более надежную проверку
    #         if instance.media_file.storage.exists(instance.media_file.name) :
    #             instance.create_preview()
    #             instance.save(update_fields=['preview_file'])
    #             logger.info(f"Превью успешно создано для {instance.pk}")
    #         else :
    #             logger.warning(f"Файл не доступен для создания превью: {instance.media_file.name}")
    #     except Exception as e :
    #         logger.error(f"Ошибка создания превью для {instance.pk}: {str(e)}")
    pass


@receiver(post_save , sender=MediaLibraryItem)
def update_media_item_metadata(sender , instance , created , **kwargs) :
    """Обновляет метаданные медиа элемента после сохранения"""
    if created and instance.media_file :
        logger.info(f"Обновление метаданных для нового медиа-элемента {instance.pk}")
        # Можно добавить дополнительную логику здесь
        # Например: автоматическое определение тегов, анализ содержимого и т.д.


@receiver(pre_delete , sender=MediaCategory)
def prevent_predefined_category_deletion(sender , instance , **kwargs) :
    """Запрещает удаление предопределенных категорий"""
    if instance.is_predefined :
        from django.core.exceptions import PermissionDenied
        logger.warning(f"Попытка удаления предопределенной категории: {instance.name}")
        raise PermissionDenied(
            f"Нельзя удалять предопределенную категорию '{instance.name}'"
        )