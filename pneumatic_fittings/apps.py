from django.apps import AppConfig


def get_this_app_name():
    return 'pneumatic_fittings'


class FittingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = get_this_app_name()
