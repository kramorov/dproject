"""
project_customers/models/system_group.py

SystemGroup — named set of system-level object permissions (Windows group analogy).
Stored in DB. Object codenames are validated against in-code OBJECT_REGISTRY.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class SystemGroup(models.Model):
    """
    Group of system permissions (like Windows group).

    object_permissions is JSON: {codename: [actions]}
    e.g.: {"admin.customers": ["view","edit"], "catalog.gearbox": ["view"]}
    """
    code = models.CharField(
        max_length=50, unique=True,
        verbose_name=_("Code"),
        help_text=_("Machine name (latin, no spaces)")
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("Name")
    )
    object_permissions = models.JSONField(
        default=dict, blank=True,
        verbose_name=_("Object permissions"),
        help_text=_("{codename: [view,edit,delete,manage]}")
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name=_("Default"),
        help_text=_("Assign to new users automatically")
    )
    sorting_order = models.IntegerField(
        default=0,
        verbose_name=_("Sorting order")
    )

    class Meta:
        verbose_name = _("System Group")
        verbose_name_plural = _("System Groups")
        ordering = ['sorting_order', 'name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    def clean(self):
        from core.object_registry import validate_permissions
        warnings = validate_permissions(self.object_permissions or {})
        # Just log warnings — don't block save
        if warnings:
            import logging
            logger = logging.getLogger(__name__)
            for w in warnings:
                logger.warning(w)

    def get_actions(self, codename: str) -> list[str]:
        """Return allowed actions for a given object codename."""
        return self.object_permissions.get(codename, [])

    def has_action(self, codename: str, action: str) -> bool:
        """Check if group has a specific action on an object."""
        perms = self.get_actions(codename)
        return action in perms or 'manage' in perms
