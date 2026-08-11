"""
configurator/services/cascade.py

Каскад параметров после выбора продукта.

1. DerivationRule: пробрасывает значения полей выбранного продукта
   в cascade_params дочерних ComponentRequirement.
2. FittingPattern: создаёт новые ComponentRequirement для фитингов
   на основе контекста монтажа.

Вызывается после select_product():
    cascade_after_select(component)
    → дочерние компоненты получают cascade_params
    → создаются CR для фитингов (если применимо)
"""
from __future__ import annotations

import logging
from typing import Optional

from django.db import models

from configurator.models import (
    ComponentRequirement,
    DerivationRule,
    FittingPattern,
)
from configurator.services.registry import get_product_model_class
from configurator.services.resolver import resolve_effective_requirements

logger = logging.getLogger(__name__)


def cascade_after_select(component: ComponentRequirement) -> dict:
    """
    Выполняет каскад после выбора продукта в component.

    1. DerivationRule: source_type → target_type
       Берёт значение source_product_field из выбранного продукта,
       записывает в cascade_params дочернего компонента.

    2. FittingPattern: создаёт новые ComponentRequirement для фитингов.

    Returns:
        {'derived_params': {child_id: {param: value}}, 'fittings_created': N}
    """
    result = {
        'derived_params': {},
        'fittings_created': 0,
    }

    if not component.selected_product_id or not component.equipment_type:
        return result

    # ── 1. DerivationRule cascade ──
    rules = DerivationRule.objects.filter(
        source_type=component.equipment_type,
        is_active=True,
    ).select_related('target_type')

    if rules:
        result['derived_params'] = _apply_derivation_rules(component, rules)

    # ── 2. FittingPattern ──
    patterns = FittingPattern.objects.filter(
        applies_to=component.equipment_type,
        is_active=True,
    ).prefetch_related('items__equipment_type')

    if patterns:
        result['fittings_created'] = _apply_fitting_patterns(component, patterns)

    return result


def _apply_derivation_rules(
    component: ComponentRequirement,
    rules: list[DerivationRule],
) -> dict[int, dict]:
    """
    Применяет DerivationRule: пробрасывает значения в дочерние компоненты.
    """
    # Получаем значения из выбранного продукта
    source_specs = component.selected_product_specs or {}
    product_field_values: dict[str, object] = {}

    for rule in rules:
        # Проверяем condition
        if rule.condition and not _check_condition(rule.condition, source_specs):
            continue

        # Получаем значение поля из продукта
        field_name = rule.source_product_field
        value = _get_nested_value(source_specs, field_name)
        if value is None:
            # Пробуем получить напрямую из БД
            value = _fetch_product_field(component, field_name)

        if value is not None:
            # Применяем transform
            value = _apply_transform(value, rule.transform)
            product_field_values[rule.target_param] = value

    if not product_field_values:
        return {}

    # Находим дочерние компоненты с target_type
    assembly = component.assembly
    child_crs = assembly.components.filter(
        parent=component,
        equipment_type__in=[r.target_type for r in rules],
        status__in=['pending', 'requirements_filled'],
    )

    result = {}
    for child in child_crs:
        child_cascade = child.cascade_params or {}
        child_cascade.update(product_field_values)
        child.cascade_params = child_cascade
        child.save(update_fields=['cascade_params'])
        result[child.id] = dict(product_field_values)

        # Пересчитываем effective_requirements
        resolve_effective_requirements(child)

    logger.info(
        "Derivation cascade: CR #%d → %d children, params=%s",
        component.id, len(result), list(product_field_values.keys()),
    )
    return result


def _apply_fitting_patterns(
    component: ComponentRequirement,
    patterns: list[FittingPattern],
) -> int:
    """
    Создаёт новые ComponentRequirement для фитингов.
    """
    assembly = component.assembly
    created_count = 0

    # Определяем максимальный path для новых компонентов
    max_order = assembly.components.aggregate(
        max_order=models.Max('order')
    )['max_order'] or 0

    for pattern in patterns:
        # Проверяем condition (контекст монтажа)
        context = component.selected_product_specs or {}
        if pattern.condition and not pattern.matches(context):
            continue

        for item in pattern.items.all():
            max_order += 1
            cr = ComponentRequirement.objects.create(
                assembly=assembly,
                equipment_type=item.equipment_type,
                composition_group_node=None,  # созданы динамически, а не из CG
                parent=component,
                path=f"{component.path}/F{max_order}",
                level=component.level + 1,
                order=max_order,
                status='pending',
                own_requirements=_resolve_fitting_config(item.config, component),
            )
            created_count += 1

    if created_count:
        logger.info(
            "FittingPattern: CR #%d → %d fitting CRs created",
            component.id, created_count,
        )
    return created_count


def _resolve_fitting_config(config: dict, component: ComponentRequirement) -> dict:
    """Разрешает ссылки на родительские параметры в конфиге фитинга."""
    resolved = {}
    source_specs = component.selected_product_specs or {}

    for key, value in config.items():
        if isinstance(value, str) and value.startswith('parent.'):
            # parent.port_size_npt → ищем в selected_product_specs
            field_path = value[7:]  # убираем 'parent.'
            resolved[key] = _get_nested_value(source_specs, field_path)
        else:
            resolved[key] = value

    return resolved


# ── Helpers ──

def _check_condition(condition: dict, specs: dict) -> bool:
    """Проверяет condition DerivationRule против specs продукта."""
    field = condition.get('field', '')
    expected = condition.get('value')
    if not field or expected is None:
        return True
    actual = _get_nested_value(specs, field)
    return str(actual) == str(expected)


def _apply_transform(value, transform: Optional[dict]) -> object:
    """Применяет transform-словарь к значению."""
    if not transform:
        return value
    mapping = transform.get('map', {})
    return mapping.get(str(value), value)


def _fetch_product_field(component: ComponentRequirement, field_name: str) -> Optional[object]:
    """Получает значение поля напрямую из БД продукта."""
    try:
        model_class = get_product_model_class(component.equipment_type)
        obj = model_class.objects.filter(id=component.selected_product_id).first()
        if obj:
            return _get_nested_attr(obj, field_name)
    except (KeyError, Exception):
        pass
    return None


def _get_nested_attr(obj, path: str):
    """Traverse nested attributes via __ (e.g. 'body__max_work_torque')."""
    parts = path.split('__')
    value = obj
    for part in parts:
        value = getattr(value, part, None)
        if value is None:
            return None
    return value


def _get_nested_value(data: dict, path: str) -> Optional[object]:
    """Извлекает значение из вложенного словаря по пути через __ или ."""
    parts = path.replace('.', '__').split('__')
    value = data
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        elif hasattr(value, part):
            value = getattr(value, part)
        else:
            return None
        if value is None:
            return None
    return value

