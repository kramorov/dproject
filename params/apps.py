from django.apps import AppConfig


def get_this_app_name():
    return 'params'


class ParamsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = get_this_app_name()
