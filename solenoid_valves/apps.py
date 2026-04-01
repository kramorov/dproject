from django.apps import AppConfig


def get_this_app_name():
    return 'solenoid_valves'


class SolenoidValvesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = get_this_app_name()
