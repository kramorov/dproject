from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class GearBoxConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gearbox'
    verbose_name = _("Редукторы")
