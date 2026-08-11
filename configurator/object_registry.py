"""
configurator/object_registry.py

Регистрирует admin-страницы конфигуратора в OBJECT_REGISTRY
для управления правами доступа через SystemGroup.
"""
from core.object_registry import register_object

# ── Админ-страницы конфигуратора ──
register_object(
    codename='configurator.rules',
    name='Правила конфигуратора',
    type='admin_page',
    parent='admin_section',
    section_code='admin_section',
)

register_object(
    codename='configurator.propagation_rules',
    name='Правила наследования (PropagationRule)',
    type='admin_page',
    parent='configurator.rules',
    section_code='admin_section',
)

register_object(
    codename='configurator.parameter_bindings',
    name='Привязки параметров (ParameterBinding)',
    type='admin_page',
    parent='configurator.rules',
    section_code='admin_section',
)

register_object(
    codename='configurator.parameter_rules',
    name='Правила параметров (ParameterRule)',
    type='admin_page',
    parent='configurator.rules',
    section_code='admin_section',
)

register_object(
    codename='configurator.derivation_rules',
    name='Правила каскада (DerivationRule)',
    type='admin_page',
    parent='configurator.rules',
    section_code='admin_section',
)
