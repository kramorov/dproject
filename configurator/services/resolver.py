"""
configurator/services/resolver.py

Вычисляет effective_requirements для ComponentRequirement.

Простой приоритет:
    1. own_requirements (пользователь) — высший приоритет
    2. global_requirements (сборка)     — средний
    3. cascade_params (DerivationRule)  — fallback

Плюс трансляция ключей: param_name → field_path
(унифицированные имена маппятся в поля БД продукта).
"""
from __future__ import annotations

import logging

from configurator.models import (
    ComponentRequirement,
    EquipmentTypeParameter,
)

logger = logging.getLogger(__name__)


def resolve_effective_requirements(component: ComponentRequirement) -> dict:
    """
    Вычисляет effective_requirements по приоритету:
        own > global > cascade.

    Транслирует ключи через EquipmentTypeParameter.field_path.
    """
    if not component.equipment_type:
        logger.warning("CR #%d: no equipment_type", component.id)
        component.effective_requirements = {}
        component.save(update_fields=['effective_requirements'])
        return {}

    assembly = component.assembly
    translation = _build_translation_map(component.equipment_type)

    # Приоритет: cascade < global < own
    effective: dict[str, object] = {}

    # 3 — cascade_params (DerivationRule fallback)
    for param, value in (component.cascade_params or {}).items():
        effective[param] = value

    # 2 — global_requirements (контекст сборки)
    for param, value in (assembly.global_requirements or {}).items():
        effective[param] = value

    # 1 — own_requirements (явное указание, высший приоритет)
    for param, value in (component.own_requirements or {}).items():
        effective[param] = value

    # Трансляция ключей
    translated = {}
    for key, value in effective.items():
        field = translation.get(key, key)
        translated[field] = value

    component.effective_requirements = translated
    component.save(update_fields=['effective_requirements'])
    return translated


def _build_translation_map(equipment_type) -> dict[str, str]:
    """param_name → field_path."""
    params = EquipmentTypeParameter.objects.filter(
        equipment_type=equipment_type,
        is_active=True,
    ).values('param_name', 'field_path')
    return {p['param_name']: p['field_path'] for p in params if p['field_path']}


def resolve_all_components(assembly) -> None:
    """Резолвит effective_requirements для всех компонентов сборки."""
    for cr in assembly.components.filter(
        equipment_type__isnull=False,
    ).select_related('equipment_type', 'parent').order_by('level', 'path'):
        resolve_effective_requirements(cr)
