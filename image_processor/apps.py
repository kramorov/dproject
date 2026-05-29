# image_processor/apps.py
from django.apps import AppConfig


class ImageProcessorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'image_processor'
    verbose_name = 'Обработка изображений'
