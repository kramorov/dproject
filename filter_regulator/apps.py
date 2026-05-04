from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class FilterRegulatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'filter_regulator'
    verbose_name = _("Фильтр-регуляторы")
