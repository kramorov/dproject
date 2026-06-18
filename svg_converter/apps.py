"""Конфигурация приложения svg_converter."""
from django.apps import AppConfig


class SvgConverterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'svg_converter'
    verbose_name = 'SVG Converter'
