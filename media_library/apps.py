# media_library/apps.py
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MediaLibraryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'media_library'
    verbose_name = _("Медиабиблиотека")

    def ready(self):
        """
        Регистрируем сигналы при запуске приложения
        """
        # Импортируем сигналы чтобы они зарегистрировались
        try:
            from . import signals
            print("Сигналы медиабиблиотеки зарегистрированы")
        except ImportError as e:
            print(f"Ошибка регистрации сигналов: {e}")