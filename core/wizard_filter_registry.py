# core/wizard_filter_registry.py
"""
Реестр FILTER_DEFINITIONS для моделей, у которых они не заданы на классе.

Некоторые модели (GearBox, DirectionValve, FilterRegulator) хранят
определения фильтров в catalog/filter_defs.py, а не как атрибут класса.
Этот реестр связывает content_type_id с соответствующим списком FilterDefinition,
чтобы WizardModelMixin._find_filter_definition() мог их найти.

НЕ модифицирует существующие модели — только читает их catalog/filter_defs.
"""
from django.contrib.contenttypes.models import ContentType


def _get_ct_id(app_label, model_name):
    """Получить content_type_id по app_label и model_name."""
    try:
        return ContentType.objects.get(app_label=app_label, model=model_name).id
    except ContentType.DoesNotExist:
        return None


# Собираем реестр: {content_type_id: [FilterDefinition, ...]}
WIZARD_FILTER_REGISTRY = {}


def _register(app_label, model_name, import_path, var_name):
    """Зарегистрировать filter_defs для модели без FILTER_DEFINITIONS на классе."""
    ct_id = _get_ct_id(app_label, model_name)
    if ct_id is None:
        return
    # Ленивый импорт — только при первом обращении
    WIZARD_FILTER_REGISTRY[ct_id] = (import_path, var_name)


# ── GearBox ──
_register('gearbox', 'gearbox',
          'gearbox.catalog.filter_defs', 'GEARBOX_FILTER_DEFINITIONS')

# ── DirectionValve (solenoid_valves) ──
_register('solenoid_valves', 'directionvalve',
          'solenoid_valves.catalog.filter_defs', 'SOLENOID_VALVES_FILTER_DEFINITIONS')

# ── FilterRegulator ──
_register('filter_regulator', 'filterregulator',
          'filter_regulator.catalog.filter_defs', 'FILTER_REGULATOR_FILTER_DEFINITIONS')

# ── LimitSwitchBox (доп. фильтры из catalog/filter_defs.py) ──
_register('pa_controls', 'limitswitchbox',
          'pa_controls.catalog.filter_defs', 'LIMIT_SWITCH_FILTER_DEFINITIONS')

# ── PneumaticFitting (доп. фильтры из catalog/filter_defs.py) ──
_register('pneumatic_fittings', 'pneumaticfitting',
          'pneumatic_fittings.catalog.filter_defs', 'PNEUMATIC_FITTINGS_FILTER_DEFINITIONS')

# ── PneumaticActuatorModelLineItem (FILTER_DEFINITIONS on class for AI pipeline) ──
_register('pneumatic_actuators', 'pneumaticactuatormodellineitem',
          None, None)


def get_filter_definitions_for_ct(content_type_id):
    """
    Получить список FilterDefinition для данного content_type_id.

    Возвращает None, если модель не в реестре (значит, нужно искать
    FILTER_DEFINITIONS на самом классе модели).
    """
    entry = WIZARD_FILTER_REGISTRY.get(content_type_id)
    if entry is None:
        return None
    import_path, var_name = entry
    if import_path is None:
        # FILTER_DEFINITIONS on the model class itself
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get(id=content_type_id)
        model_class = ct.model_class()
        if model_class and hasattr(model_class, 'FILTER_DEFINITIONS'):
            return model_class.FILTER_DEFINITIONS
        return None
    import importlib
    module = importlib.import_module(import_path)
    return getattr(module, var_name, [])
