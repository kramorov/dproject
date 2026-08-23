"""
pneumatic_actuators/object_registry.py — System objects for pneumatic actuators.
"""
from core.object_registry import register_object

# Конфигураторы
register_object(codename='configurator.pa', name='Конфигуратор пневмоприводов', type='configurator', parent='configurators')
register_object(codename='selector.pa', name='Подбор пневмопривода', type='configurator', parent='configurators')

# Каталоги
register_object(codename='catalog.pa', name='Каталог пневмоприводов', type='catalog', parent='catalogs')
register_object(codename='catalog.filter_regulator', name='Каталог фильтр-регуляторов', type='catalog', parent='catalogs', section_code='catalog_fr')
register_object(codename='catalog.solenoid_valves', name='Каталог соленоидных клапанов', type='catalog', parent='catalogs', section_code='catalog_sv')
register_object(codename='catalog.pneumatic_fittings', name='Каталог пневмофитингов', type='catalog', parent='catalogs', section_code='catalog_pf')
register_object(codename='catalog.pneumatic_silencers', name='Каталог пневмоглушителей', type='catalog', parent='catalogs', section_code='catalog_sil')
register_object(codename='catalog.pneumatic_plugs', name='Каталог пневмозаглушек', type='catalog', parent='catalogs', section_code='catalog_plug')
register_object(codename='catalog.limit_switch', name='Каталог БКВ', type='catalog', parent='catalogs', section_code='catalog_lsb')
register_object(codename='catalog.gearbox', name='Каталог ручных дублёров', type='catalog', parent='catalogs')
