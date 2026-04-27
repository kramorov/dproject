from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class PaControlsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pa_controls'
    verbose_name = _("Устройства для управления ПП")
