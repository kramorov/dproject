"""
configurator/services/registry.py

Реестр: EquipmentType.code → Django model class.

Используется FilterEngine и другими сервисами для получения
model_class по equipment_type при построении Q-фильтров.

Источник данных: CatalogConfig.model_class из каждого каталога.
"""
from __future__ import annotations

from django.apps import apps
from django.db.models import Model

# ── Статический реестр ──
# Формат: 'equipment_type_code' → ('app_label', 'ModelName')
PRODUCT_MODEL_REGISTRY: dict[str, tuple[str, str]] = {
    'pneumatic-actuator':  ('pneumatic_actuators', 'PneumaticActuatorModelLineItem'),
    'directional-valve':   ('solenoid_valves', 'DirectionValve'),
    'lsb':                 ('pa_controls', 'LimitSwitchBox'),
    'fr':                  ('filter_regulator', 'FilterRegulator'),
    'manual-override':     ('gearbox', 'GearBox'),
    'cable-gland':         ('cable_glands', 'CableGlandItem'),
    'fittings':            ('pneumatic_fittings', 'PneumaticFitting'),
    # Арматура — будет добавлена позже, когда будет готова модель
}

# ── Кэш загруженных моделей ──
_model_cache: dict[str, type[Model]] = {}


def get_product_model_class(equipment_type) -> type[Model]:
    """
    EquipmentType → Django model class.

    Args:
        equipment_type: EquipmentType instance или строка equipment_type.code.

    Returns:
        Django model class (например, GearBox).

    Raises:
        KeyError: если equipment_type.code отсутствует в реестре.
    """
    from core.models import EquipmentType

    if isinstance(equipment_type, EquipmentType):
        code = equipment_type.code
    elif isinstance(equipment_type, str):
        code = equipment_type
    else:
        raise TypeError(f"Expected EquipmentType or str, got {type(equipment_type)}")

    if code in _model_cache:
        return _model_cache[code]

    entry = PRODUCT_MODEL_REGISTRY.get(code)
    if not entry:
        raise KeyError(
            f"EquipmentType code '{code}' not found in PRODUCT_MODEL_REGISTRY. "
            f"Known codes: {list(PRODUCT_MODEL_REGISTRY.keys())}"
        )

    app_label, model_name = entry
    model_class = apps.get_model(app_label, model_name)
    _model_cache[code] = model_class
    return model_class


def register_product_model(equipment_type_code: str, app_label: str, model_name: str) -> None:
    """Динамически зарегистрировать model_class для equipment_type_code."""
    PRODUCT_MODEL_REGISTRY[equipment_type_code] = (app_label, model_name)
    _model_cache.pop(equipment_type_code, None)
