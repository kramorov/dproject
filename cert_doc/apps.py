from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class CertDocConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cert_doc'
    verbose_name = _('Сертификаты')
