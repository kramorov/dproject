"""
configurator/services/cascade.py

Каскад параметров после выбора продукта.

Единая точка входа: `cascade_after_select(component)`.

1. DerivationRule: пробрасывает значения полей выбранного продукта
   в cascade_params дочерних ComponentRequirement.
2. FittingPattern: создаёт новые ComponentRequirement для фитингов
   на основе контекста монтажа.

Ядро каскада — `resolve_derivation_params(...)` — чистая функция,
которая по паре (source_type, target_type) вычисляет словарь
{target_param: value}. Её переиспользуют оба дерева подбора:
- ComponentRequirement (configurator) — через cascade_after_select;
- SelectionNode (ai_assistant) — через TreeProcessor.select_product.
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


def resolve_derivation_params(
    source_type,
    target_type,
    source_specs: dict,
    product_id: Optional[int] = None,
) -> dict:
    """
    Вычисляет cascade_params для пары типов (source_type → target_type).

    Это общее ядро каскада — не зависит от модели дерева (ComponentRequirement
    или SelectionNode). Переиспользуется обоими каскадами.

    Args:
        source_type: EquipmentType источника (родитель).
        target_type: EquipmentType приёмника (ребёнок).
        source_specs: dict характеристик выбранного продукта (плоский __dict__
            или вложенный по `__` путям).
        product_id: ID выбранного продукта — для fallback в БД, если значение
            не найдено в source_specs.

    Returns:
        {target_param: value} — значения, проброшенные из источника. Пустой dict,
        если правил для пары нет или ни одно не сработало.
    """
    rules = DerivationRule.objects.filter(
        source_type=source_type,
        target_type=target_type,
        is_active=True,
    ).order_by("priority")

    params: dict[str, object] = {}
    for rule in rules:
        # Условие срабатывания
        if rule.condition and not _check_condition(rule.condition, source_specs):
            continue

        # Значение из спецификации продукта (вложенные пути через __)
        value = _get_nested_value(source_specs, rule.source_product_field)

        # Fallback: напрямую из БД продукта
        if value is None and product_id is not None:
            value = _fetch_product_field(source_type, product_id, rule.source_product_field)

        if value is not None:
            params[rule.target_param] = _apply_transform(value, rule.transform)

    return params


def cascade_after_select(component: ComponentRequirement) -> dict:
    """
    Выполняет каскад после выбора продукта в component.

    1. DerivationRule: source_type → target_type.
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
    result['derived_params'] = _apply_derivation_rules(component)

    # ── 2. FittingPattern ──
    patterns = FittingPattern.objects.filter(
        applies_to=component.equipment_type,
        is_active=True,
    ).prefetch_related('items__equipment_type')

    if patterns:
        result['fittings_created'] = _apply_fitting_patterns(component, patterns)

    return result


def _apply_derivation_rules(component: ComponentRequirement) -> dict[int, dict]:
    """
    Применяет DerivationRule: для каждого дочернего компонента вычисляет
    cascade_params через resolve_derivation_params.
    """
    source_specs = component.selected_product_specs or {}
    assembly = component.assembly

    child_crs = assembly.components.filter(
        parent=component,
        status__in=['pending', 'requirements_filled'],
    ).select_related('equipment_type')

    result = {}
    for child in child_crs:
        if not child.equipment_type:
            continue

        params = resolve_derivation_params(
            source_type=component.equipment_type,
            target_type=child.equipment_type,
            source_specs=source_specs,
            product_id=component.selected_product_id,
        )
        if not params:
            continue

        child_cascade = child.cascade_params or {}
        child_cascade.update(params)
        child.cascade_params = child_cascade
        child.save(update_fields=['cascade_params'])
        result[child.id] = dict(params)

        # Пересчитываем effective_requirements
        resolve_effective_requirements(child)

    if result:
        logger.info(
            "Derivation cascade: CR #%d → %d children",
            component.id, len(result),
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

    # Определяем максимальный order для новых компонентов
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


def _fetch_product_field(source_type, product_id: int, field_name: str) -> Optional[object]:
    """Получает значение поля напрямую из БД продукта."""
    try:
        model_class = get_product_model_class(source_type)
        if model_class is None:
            return None
        obj = model_class.objects.filter(id=product_id).first()
        if obj:
            return _get_nested_attr(obj, field_name)
    except Exception:
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
