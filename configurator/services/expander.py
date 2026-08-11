"""
configurator/services/expander.py

Разворачивает CompositionGroup в дерево ComponentRequirement.

Вызывается при создании AssemblyRequirements:
    assembly = AssemblyRequirements(composition_group=pa_kit)
    expand_composition_group(assembly)
    → создаёт дерево ComponentRequirement
"""
from __future__ import annotations

import logging
from typing import Optional

from django.db import transaction

from ai_assistant.models import CompositionGroup
from configurator.models import AssemblyRequirements, ComponentRequirement

logger = logging.getLogger(__name__)


def expand_composition_group(
    assembly: AssemblyRequirements,
    root_node: Optional[CompositionGroup] = None,
) -> list[ComponentRequirement]:
    """
    Разворачивает CompositionGroup — создаёт дерево ComponentRequirement.

    Args:
        assembly: AssemblyRequirements, к которой привязать компоненты.
        root_node: Опциональная точка входа. Если не указана — используется
                   assembly.root_node или assembly.composition_group.

    Returns:
        Список созданных ComponentRequirement (корневые узлы).

    Алгоритм:
        1. Определяем точку входа (root_node или composition_group)
        2. Рекурсивно обходим дерево CompositionGroup
        3. Для каждого узла создаём ComponentRequirement для каждого equipment_type
        4. Обрабатываем references (ссылки на другие группы) с защитой от циклов
        5. Устанавливаем parent/child, path, level, order
    """
    entry = root_node or assembly.root_node or assembly.composition_group
    if not entry:
        raise ValueError("Assembly has no composition_group and no root_node")

    created: list[ComponentRequirement] = []

    with transaction.atomic():
        # Удаляем существующие компоненты, если переразворачиваем
        assembly.components.all().delete()

        _expand_node(
            cg_node=entry,
            assembly=assembly,
            parent_cr=None,
            created=created,
            path_prefix="",
            level=1,
            order_counter=[0],
            seen=set(),
        )

    logger.info(
        "Expanded CompositionGroup '%s' → %d ComponentRequirements for assembly #%d",
        entry.code or entry.name or entry.id,
        len(created),
        assembly.id,
    )
    return created


def _expand_node(
    cg_node: CompositionGroup,
    assembly: AssemblyRequirements,
    parent_cr: Optional[ComponentRequirement],
    created: list[ComponentRequirement],
    path_prefix: str,
    level: int,
    order_counter: list[int],
    seen: set[int],
) -> None:
    """
    Рекурсивно создаёт ComponentRequirement для одного узла CompositionGroup
    и всех его потомков (children + references).
    """
    # Защита от циклов (references)
    if cg_node.id in seen:
        logger.warning("Cycle detected in CompositionGroup references: node #%d already visited", cg_node.id)
        return
    seen.add(cg_node.id)

    # ── 1. EquipmentTypes этого узла ──
    equipment_types = list(
        cg_node.equipment_types.filter(is_active=True).order_by('sorting_order', 'code')
    )

    for idx, et in enumerate(equipment_types):
        order_counter[0] += 1
        path = f"{path_prefix}{order_counter[0]}"

        cr = ComponentRequirement.objects.create(
            assembly=assembly,
            equipment_type=et,
            composition_group_node=cg_node,
            parent=parent_cr,
            path=path,
            level=level,
            order=order_counter[0],
            status='pending',
        )
        created.append(cr)

    # ── Определяем parent для дочерних групп ──
    # Если у узла есть equipment_types → последний CR становится родителем.
    # Если нет → создаём виртуальный узел для сохранения иерархии.
    children_parent: Optional[ComponentRequirement] = parent_cr

    if equipment_types:
        children_parent = created[-1]  # последний CR = родитель для потомков
    else:
        children = list(
            cg_node.children.filter(is_active=True).order_by('sorting_order', 'name')
        )
        refs = list(
            cg_node.references.filter(is_active=True).order_by('sorting_order', 'name')
        )
        if children or refs:
            order_counter[0] += 1
            path = f"{path_prefix}{order_counter[0]}"
            virtual_cr = ComponentRequirement.objects.create(
                assembly=assembly,
                equipment_type=None,
                composition_group_node=cg_node,
                parent=parent_cr,
                path=path,
                level=level,
                order=order_counter[0],
                status='pending',
            )
            created.append(virtual_cr)
            children_parent = virtual_cr

    # ── 2. Дочерние CompositionGroup (вложенность) ──
    child_path_prefix = f"{children_parent.path}/" if children_parent else ""
    for child_cg in cg_node.children.filter(is_active=True).order_by('sorting_order', 'name'):
        _expand_node(
            cg_node=child_cg,
            assembly=assembly,
            parent_cr=children_parent,
            created=created,
            path_prefix=child_path_prefix,
            level=level + 1,
            order_counter=order_counter,
            seen=seen,
        )

    # ── 3. References (ссылки на другие группы) ──
    ref_path_prefix = f"{children_parent.path}/" if children_parent else ""
    for ref_cg in cg_node.references.filter(is_active=True).order_by('sorting_order', 'name'):
        _expand_node(
            cg_node=ref_cg,
            assembly=assembly,
            parent_cr=children_parent,
            created=created,
            path_prefix=ref_path_prefix,
            level=level + 1,
            order_counter=order_counter,
            seen=seen,
        )
