from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EaControlConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ea_control'
    verbose_name = _("Блоки управления ЭП")
