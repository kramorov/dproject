"""
pa_controls/object_registry.py — System objects for PA controls (позиционеры, БКВ).

Registered at import time via core.object_registry.register_object().
Objects appear in the /admin/permissions matrix and get auto-synced permissions.
"""
from core.object_registry import register_object

# Каталоги
register_object(
    codename='catalog.positioners',
    name='Каталог позиционеров',
    type='catalog',
    parent='catalogs',
    section_code='catalog_positioners',
)
