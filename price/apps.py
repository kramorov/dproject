from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class PriceConfig(AppConfig) :
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'price'
    verbose_name = _('Цены')
