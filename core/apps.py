# core/apps.py
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Ядро системы'

    def ready(self):
        self._import_object_registries()
        self._connect_signals()

    def _import_object_registries(self):
        """Auto-import object_registry.py from every installed app."""
        import importlib
        import logging

        logger = logging.getLogger(__name__)
        for app_config in self.apps.get_app_configs():
            try:
                importlib.import_module(f'{app_config.name}.object_registry')
                logger.debug(f'Loaded object_registry: {app_config.name}')
            except ImportError:
                pass  # No object_registry in this app — normal

    def _connect_signals(self):
        """Connect post_migrate signal for admin permission sync."""
        from django.db.models.signals import post_migrate
        post_migrate.connect(self._sync_admin_permissions, sender=self)
        post_migrate.connect(self._sync_anonymous_permissions, sender=self)
        self._connect_cache_invalidation()

    @staticmethod
    def _sync_admin_permissions(sender, **kwargs):
        """Auto-sync administrators group: every registered object gets manage."""
        import logging
        from core.object_registry import OBJECT_REGISTRY

        logger = logging.getLogger(__name__)
        try:
            from project_customers.models import SystemGroup
            group = SystemGroup.objects.filter(code='administrators').first()
            if group is None:
                return

            perms = group.object_permissions or {}
            updated = False

            for codename in OBJECT_REGISTRY:
                if codename not in perms or 'manage' not in perms[codename]:
                    perms[codename] = ['manage']
                    updated = True

            stale = [c for c in perms if c not in OBJECT_REGISTRY]
            for c in stale:
                del perms[c]
                updated = True

            if updated:
                group.object_permissions = perms
                group.save(update_fields=['object_permissions'])
                logger.info(
                    f'Synced administrators: {len(OBJECT_REGISTRY)} objects, '
                    f'removed {len(stale)} stale'
                )
            from core.utils.permission_helpers import clear_permission_cache
            clear_permission_cache()
        except Exception:
            pass  # DB not ready yet

    @staticmethod
    def _sync_anonymous_permissions(sender, **kwargs):
        """Auto-sync anonymous_users group: catalog/configurator objects get view."""
        import logging
        from core.object_registry import OBJECT_REGISTRY

        logger = logging.getLogger(__name__)
        try:
            from project_customers.models import SystemGroup
            group = SystemGroup.objects.filter(code='anonymous_users').first()
            if group is None:
                return

            perms = group.object_permissions or {}
            updated = False

            # Grant view on all catalog and configurator objects
            for codename, obj_def in OBJECT_REGISTRY.items():
                if obj_def.type in ('catalog', 'configurator'):
                    if codename not in perms:
                        perms[codename] = ['view']
                        updated = True
                    elif 'view' not in perms[codename] and 'manage' not in perms[codename]:
                        perms[codename] = list(set(perms[codename]) | {'view'})
                        updated = True

            # Remove stale entries (objects no longer in registry)
            stale = [c for c in perms if c not in OBJECT_REGISTRY]
            for c in stale:
                del perms[c]
                updated = True

            if updated:
                group.object_permissions = perms
                group.save(update_fields=['object_permissions'])
                logger.info(
                    f'Synced anonymous_users: {len([c for c in OBJECT_REGISTRY if OBJECT_REGISTRY[c].type in ("catalog","configurator")])} objects with view'
                )
            from core.utils.permission_helpers import clear_permission_cache
            clear_permission_cache()
        except Exception:
            pass  # DB not ready yet

    @staticmethod
    def _connect_cache_invalidation():
        """Invalidate permission cache when any SystemGroup is saved."""
        from django.db.models.signals import post_save, post_delete
        from core.utils.permission_helpers import clear_permission_cache
        try:
            from project_customers.models import SystemGroup
        except Exception:
            return  # Models not ready yet

        def _on_group_change(sender, instance, **kwargs):
            clear_permission_cache()

        post_save.connect(_on_group_change, sender=SystemGroup)
        post_delete.connect(_on_group_change, sender=SystemGroup)
