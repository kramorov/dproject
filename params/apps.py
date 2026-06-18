from django.apps import AppConfig


def get_this_app_name():
    return 'params'


class ParamsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = get_this_app_name()

    def ready(self):
        # Админки из отдельных файлов — регистрируются после загрузки
        # всех приложений, чтобы избежать циклических импортов.
        from . import admin_turn_counter  # noqa: F401
        from . import admin_signal        # noqa: F401