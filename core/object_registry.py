"""
core/object_registry.py — Central Object Registry.

Holds the canonical list of all system objects (pages, APIs, UI elements, configurators, catalogs).
Stored in code, not in the database. The database stores only permissions (SystemGroup.object_permissions).

Usage:
    from core.object_registry import register_object, OBJECT_REGISTRY

    register_object(
        codename='configurator.pa',
        name='Конфигуратор пневмоприводов',
        type='configurator',
        parent='configurators',
    )

Objects are registered at import time from <app>/object_registry.py files.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ObjectDef:
    codename: str
    name: str
    type: str          # 'page' | 'api' | 'ui_element' | 'configurator' | 'catalog' | 'admin_page'
    parent: Optional[str] = None


# Canonical registry: {codename: ObjectDef}
OBJECT_REGISTRY: dict[str, ObjectDef] = {}


def register_object(
    *,
    codename: str,
    name: str,
    type: str,
    parent: Optional[str] = None,
) -> ObjectDef:
    """
    Register a system object in the canonical registry.

    Called from <app>/object_registry.py at import time.
    Duplicate codenames are silently overwritten (last registration wins).
    """
    obj = ObjectDef(codename=codename, name=name, type=type, parent=parent)
    OBJECT_REGISTRY[codename] = obj
    return obj


def get_registry() -> dict[str, ObjectDef]:
    """Return a copy of the current registry."""
    return dict(OBJECT_REGISTRY)


def get_registry_as_list() -> list[dict]:
    """Return registry as a list of dicts (for API responses)."""
    return [
        {
            'codename': v.codename,
            'name': v.name,
            'type': v.type,
            'parent': v.parent,
        }
        for v in OBJECT_REGISTRY.values()
    ]


def validate_permissions(permissions: dict) -> list[str]:
    """
    Validate a permissions dict against the registry.
    Returns list of warnings (unknown codenames).
    Callers should log or surface these warnings.
    """
    return [f"Unknown object: '{c}'" for c in permissions if c not in OBJECT_REGISTRY]
