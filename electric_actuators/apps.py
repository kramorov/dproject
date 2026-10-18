"""Конфигурация приложения electric_actuators."""
from django.apps import AppConfig


class ElectricActuatorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'electric_actuators'

    def ready(self):
        from django.db.models.signals import m2m_changed

        def recalc_catalog_item(sender, instance, action, **kwargs):
            """M2M matrix_rows изменился → пересобрать code/name/description
            карточки (хэш уже пересчитан ресивером core.ConfigHashMixin)."""
            if action not in ('post_add', 'post_remove', 'post_clear'):
                return
            model = type(instance)
            if model.__name__ != 'ElectricActuatorCatalogItem':
                return
            try:
                instance.update_name(save=False)
                instance.update_description(save=False)
                code = instance.generated_article()
                model.objects.filter(pk=instance.pk).update(
                    name=instance.name, description=instance.description,
                    code=code or instance.code)
            except Exception:
                pass

        from electric_actuators.models import ElectricActuatorCatalogItem
        m2m_changed.connect(
            recalc_catalog_item,
            sender=ElectricActuatorCatalogItem.matrix_rows.through)
