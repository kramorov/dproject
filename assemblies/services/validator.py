"""Сервис validate_requirements — валидация требований по EquipmentTypeParameter (ETP).

Проверяет:
  - неизвестные ключи (нет в ETP для типа);
  - обязательные параметры (is_required=True) присутствуют.
"""
from __future__ import annotations

from configurator.models import EquipmentTypeParameter


def validate_requirements(equipment_type, requirements: dict) -> dict:
    """Валидирует требования компонента по ETP.

    Returns:
        {'is_valid': bool, 'errors': [str], 'missing_required': [str]}
    """
    if equipment_type is None:
        return {"is_valid": False, "errors": ["no equipment_type"], "missing_required": []}

    requirements = requirements or {}
    etps = EquipmentTypeParameter.objects.filter(
        equipment_type=equipment_type, is_active=True
    )
    known = {p.param_name for p in etps}

    errors = [f"Неизвестный параметр: {key}" for key in requirements if key not in known]
    missing = [
        p.param_name
        for p in etps
        if p.is_required and requirements.get(p.param_name) in (None, "", [])
    ]

    return {
        "is_valid": not errors and not missing,
        "errors": errors,
        "missing_required": missing,
    }
