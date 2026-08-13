"""Сервис materialize_mbom — материализация MBOM из закреплённой сборки.

MBOM — проекция fixed-сборки в SKU-структуру для КП/счёта.
Порождается только из `fixed`-сборки; не редактируется отдельно.
"""
from __future__ import annotations

from django.db import transaction


def materialize_mbom(fixed_assembly, *, name: str | None = None, code: str | None = None):
    """Материализует MBOM из закреплённой (fixed) сборки.

    Обходит дерево компонентов в порядке создания (order), создаёт MBOMItem
    для каждого включённого (`included=True`) узла. `selected_sku` попадает в
    MBOMItem.sku; составные узлы (sku=null) сохраняются как структурные узлы.

    Идемпотентность: детерминированный code — повторный вызов возвращает
    существующий MBOM, не плодит дубликаты.
    """
    from sku.models import MBOM, MBOMItem

    if fixed_assembly.status != "fixed":
        raise ValueError("MBOM можно материализовать только из fixed-сборки")

    code = code or f"assembly-{fixed_assembly.id}"

    with transaction.atomic():
        mbom, created = MBOM.objects.get_or_create(
            code=code,
            defaults={
                "name": name or fixed_assembly.name or f"MBOM {fixed_assembly.id}",
                "description": f"Материализован из сборки #{fixed_assembly.id}",
            },
        )
        if not created:
            return mbom  # уже материализован — идемпотентно

        parent_map: dict[int | None, MBOMItem | None] = {None: None}
        for cr in fixed_assembly.components.filter(included=True).order_by("order", "path"):
            item = MBOMItem.objects.create(
                mbom=mbom,
                parent=parent_map.get(cr.parent_id),
                equipment_type=cr.equipment_type,
                composition_group=cr.composition_group_node,
                sku=cr.selected_sku,  # null для составного узла
                quantity=1,
                position=cr.order,
            )
            parent_map[cr.id] = item

    return mbom
