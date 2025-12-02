# core/apps.py
from django.apps import AppConfig


class CoreConfig(AppConfig) :
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Ядро системы'

    def ready(self) :
        # Импортируем сигналы
        import core.signals