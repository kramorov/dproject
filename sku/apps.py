# sku/apps.py
from django.apps import AppConfig


class SkuConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sku'
    verbose_name = 'SKU (Номенклатура)'
