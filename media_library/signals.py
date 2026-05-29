import logging
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .models import MediaCategory

logger = logging.getLogger(__name__)


@receiver(pre_delete, sender=MediaCategory)
def prevent_predefined_category_deletion(sender, instance, **kwargs):
    """Запрещает удаление предопределенных категорий."""
    if instance.is_predefined:
        from django.core.exceptions import PermissionDenied
        logger.warning(f"Попытка удаления предопределенной категории: {instance.name}")
        raise PermissionDenied(
            f"Нельзя удалять предопределенную категорию '{instance.name}'"
        )
