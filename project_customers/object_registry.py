"""
project_customers/object_registry.py — System objects for customer management.

Registered at import time via core.object_registry.register_object().
These objects appear in the /admin/permissions matrix.
"""
from core.object_registry import register_object

# === Администрирование (admin pages) ===

register_object(
    codename='admin.customers',
    name='Управление клиентами',
    type='admin_page',
    parent='admin',
)

register_object(
    codename='admin.permissions',
    name='Права доступа',
    type='admin_page',
    parent='admin',
)

register_object(
    codename='admin.media',
    name='Медиабиблиотека',
    type='admin_page',
    parent='admin',
)

register_object(
    codename='admin.sku',
    name='Управление SKU',
    type='admin_page',
    parent='admin',
)

register_object(
    codename='admin.prices',
    name='Управление ценами',
    type='admin_page',
    parent='admin',
)

register_object(
    codename='admin.certs',
    name='Управление сертификатами',
    type='admin_page',
    parent='admin',
)
