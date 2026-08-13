"""Сервис resolution — разрешение «текущей» сборки и цепочки состава."""
from __future__ import annotations

from assemblies.models import AssemblyRequirements


def get_current_assembly(requirement_version):
    """Текущая сборка для версии требований: draft, иначе последний fixed."""
    qs = AssemblyRequirements.objects.filter(requirement_version=requirement_version)
    draft = qs.filter(status="draft").order_by("-created_at").first()
    if draft:
        return draft
    return qs.filter(status="fixed").order_by("-revision").first()


def get_assembly_chain(assembly: AssemblyRequirements) -> list[AssemblyRequirements]:
    """Цепочка состава (parent_assembly): от текущей к корню линии."""
    chain = []
    current = assembly
    seen = set()
    while current and current.id not in seen:
        seen.add(current.id)
        chain.append(current)
        current = current.parent_assembly
    return chain
