"""Сервис fork_assembly — полное глубокое копирование сборки.

Правила линий версионирования:
  - требования изменились → requirement_version=новая, parent_assembly=None;
  - состав изменился (требования те же) → requirement_version=та же, parent_assembly=source.
"""
from __future__ import annotations

import copy

from django.db import transaction

from assemblies.models import AssemblyRequirements, ComponentRequirement


def fork_assembly(
    source: AssemblyRequirements,
    *,
    for_requirements_change: bool = False,
    new_requirement_version=None,
) -> AssemblyRequirements:
    """Глубоко копирует сборку (дерево + требования + выбор) в новый draft.

    Args:
        source: исходная сборка.
        for_requirements_change: True — копия под новую версию требований
            (requirement_version=new_requirement_version, parent_assembly=None).
            False — копия состава под те же требования (parent_assembly=source).
        new_requirement_version: новая версия требований (при for_requirements_change=True).

    Returns:
        Новая AssemblyRequirements (draft).
    """
    if for_requirements_change:
        requirement_version = new_requirement_version
        parent_assembly = None
    else:
        requirement_version = source.requirement_version
        parent_assembly = source

    with transaction.atomic():
        clone = AssemblyRequirements.objects.create(
            name=source.name,
            composition_group=source.composition_group,
            root_node=source.root_node,
            global_requirements=copy.deepcopy(source.global_requirements or {}),
            status="draft",
            revision=None,
            parent_assembly=parent_assembly,
            is_template=False,
            requirement_version=requirement_version,
            conversation=source.conversation,
        )

        _clone_components(source, clone)

    return clone


def _clone_components(source: AssemblyRequirements, clone: AssemblyRequirements) -> None:
    """Копирует дерево компонентов с пересчётом parent-ссылок.

    Компоненты обходятся по `order` (глобальный счётчик создания в expander),
    поэтому родитель гарантированно клонируется раньше ребёнка.
    """
    parent_map: dict[int | None, ComponentRequirement | None] = {None: None}

    components = list(source.components.order_by("order", "path"))
    for cr in components:
        new_cr = ComponentRequirement.objects.create(
            assembly=clone,
            equipment_type=cr.equipment_type,
            composition_group_node=cr.composition_group_node,
            parent=parent_map.get(cr.parent_id),
            path=cr.path,
            level=cr.level,
            order=cr.order,
            included=cr.included,
            own_requirements=copy.deepcopy(cr.own_requirements or {}),
            effective_requirements=copy.deepcopy(cr.effective_requirements or {}),
            cascade_params=copy.deepcopy(cr.cascade_params),
            filter_results=copy.deepcopy(cr.filter_results),
            selected_sku=cr.selected_sku,
            selected_product_specs=copy.deepcopy(cr.selected_product_specs),
            status=cr.status,
        )
        parent_map[cr.id] = new_cr
