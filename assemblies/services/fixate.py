"""Сервис fixate — закрепление сборки (draft → fixed).

Guard: все узлы должны быть в терминальном статусе (selected или skipped).
revision = глубина цепочки состава (parent_assembly) + 1:
    первая сборка линии → 1, следующий fork состава → 2, ...
    смена требований (parent_assembly=None) сбрасывает к 1.
"""
from __future__ import annotations

from django.utils import timezone

from assemblies.models import AssemblyRequirements

TERMINAL_STATUSES = ("selected", "skipped")


def fixate(assembly: AssemblyRequirements, *, user=None, comment: str = "") -> AssemblyRequirements:
    """Закрепляет draft → fixed (смена статуса той же записи, без копии).

    Raises:
        ValueError: если не все узлы в терминальном статусе.
    """
    if assembly.status == "fixed":
        return assembly  # идемпотентно — повторный вызов не создаёт дубль revision

    unresolved = assembly.components.exclude(status__in=TERMINAL_STATUSES).count()
    if unresolved:
        raise ValueError(
            f"Нельзя закрепить сборку #{assembly.id}: "
            f"{unresolved} узлов не в терминальном статусе ({'/'.join(TERMINAL_STATUSES)})"
        )

    assembly.status = "fixed"
    assembly.revision = _chain_depth(assembly) + 1
    assembly.fixed_at = timezone.now()
    assembly.fixed_by = user
    assembly.fixation_comment = comment
    assembly.save(
        update_fields=[
            "status", "revision", "fixed_at", "fixed_by",
            "fixation_comment", "updated_at",
        ]
    )
    return assembly


def _chain_depth(assembly: AssemblyRequirements) -> int:
    """Глубина цепочки состава (число предков через parent_assembly)."""
    depth = 0
    current = assembly
    seen = set()
    while current.parent_assembly_id and current.parent_assembly_id not in seen:
        seen.add(current.parent_assembly_id)
        current = current.parent_assembly
        depth += 1
    return depth
