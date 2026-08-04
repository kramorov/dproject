"""
electric_actuators/object_registry.py — System objects for electric actuators.
"""
from core.object_registry import register_object

register_object(codename='configurator.ea', name='Конфигуратор электроприводов', type='configurator', parent='configurators')
register_object(codename='configurator.ea_cabinets', name='Конфигуратор шкафов управления ЭП', type='configurator', parent='configurators')
register_object(codename='configurator.ea_assemblies', name='Конфигуратор сборок арматуры с ЭП', type='configurator', parent='configurators')
register_object(codename='catalog.ea', name='Каталог электроприводов', type='catalog', parent='catalogs')
register_object(codename='catalog.ea_reducers', name='Каталог редукторов к ЭП', type='catalog', parent='catalogs')
