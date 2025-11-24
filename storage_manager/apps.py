# storage_manager/apps.py
from django.apps import AppConfig

class StorageManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'storage_manager'
    verbose_name = 'Менеджер хранилища'