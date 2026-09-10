"""
cable_glands/object_registry.py — System objects for cable glands.
"""
from core.object_registry import register_object

register_object(codename='configurator.cg', name='Конфигуратор кабельных вводов', type='configurator', parent='configurators')
register_object(codename='catalog.cg', name='Каталог кабельных вводов', type='catalog', parent='catalogs')
