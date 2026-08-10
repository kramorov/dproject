"""
configurator/object_registry.py — System objects for equipment configurator.

Registers admin pages and UI objects in the central OBJECT_REGISTRY.
These objects appear in the /admin/permissions matrix and TopMenu.
"""
from core.object_registry import register_object

# Admin pages — parent='configurator' groups them in the TopMenu
register_object(
    codename='configurator.assembly_requirements',
    name='Сессии подбора',
    type='admin_page',
    parent='configurator',
)
register_object(
    codename='configurator.component_requirement',
    name='Компоненты сборок',
    type='admin_page',
    parent='configurator',
)
register_object(
    codename='configurator.propagation_rule',
    name='Правила наследования',
    type='admin_page',
    parent='configurator',
)
register_object(
    codename='configurator.derivation_rule',
    name='Правила каскада',
    type='admin_page',
    parent='configurator',
)
register_object(
    codename='configurator.parameter_rule',
    name='Правила параметров',
    type='admin_page',
    parent='configurator',
)
register_object(
    codename='configurator.parameter_binding',
    name='Привязки параметров',
    type='admin_page',
    parent='configurator',
)
register_object(
    codename='configurator.fitting_pattern',
    name='Шаблоны фитингов',
    type='admin_page',
    parent='configurator',
)

# Configurator parent group (for TopMenu nesting)
register_object(
    codename='configurator',
    name='Конфигуратор',
    type='admin_page',
    parent=None,
)
