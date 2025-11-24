from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ValveDataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'valve_data'
    verbose_name = _("Арматура")

    def ready(self):
        # Импортируем сигналы, если они есть
        try:
            from . import signals
        except ImportError:
            pass