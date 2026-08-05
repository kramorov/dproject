"""
core/permissions.py — DRF permission classes.

SystemObjectPermission  — system-level: checks group object_permissions
                        Also checks anonymous_users SystemGroup for unauthenticated users.
OrgSectionPermission    — organization-level: checks SiteSection access
"""
from rest_framework.permissions import BasePermission


class SystemObjectPermission(BasePermission):
    """
    System-level permission check via Object Registry + SystemGroup.

    Usage:
        class MyView(APIView):
            permission_classes = [IsAuthenticated, SystemObjectPermission]
            required_object = 'admin.customers'
            required_action = 'view'
    """

    def has_permission(self, request, view):
        obj = getattr(view, 'required_object', None)
        action = getattr(view, 'required_action', 'view')

        if obj is None:
            return True  # Not a system-protected endpoint

        if not request.user.is_authenticated:
            # Check anonymous_users SystemGroup
            from core.utils.permission_helpers import get_anonymous_group
            anon_group = get_anonymous_group()
            if anon_group:
                perms = anon_group.object_permissions.get(obj, [])
                if action in perms or 'manage' in perms:
                    return True
            return False

        if request.user.is_superuser:
            return True

        from project_customers.utils import get_customer_profile
        profile = get_customer_profile(request)
        if not profile:
            return False

        return profile.has_system_perm(obj, action)


class OrgSectionPermission(BasePermission):
    """
    Organization-level permission check via SiteSection.
    Also checks anonymous_users SystemGroup for unauthenticated users.

    Usage:
        class MyView(APIView):
            permission_classes = [IsAuthenticated, OrgSectionPermission]
            required_section = 'catalog_gearbox'
            public = False  # True = allow anonymous
    """

    def has_permission(self, request, view):
        # Public endpoints — open to all
        if getattr(view, 'public', False):
            return True

        # Not authenticated — check anonymous_users SystemGroup
        if not request.user or not request.user.is_authenticated:
            required_section = getattr(view, 'required_section', None)
            if not required_section:
                return False

            # Map HTTP method to required action
            method = request.method
            if method in ('GET', 'HEAD', 'OPTIONS'):
                required_action = 'view'
            elif method in ('POST', 'PUT', 'PATCH'):
                required_action = 'edit'
            elif method == 'DELETE':
                required_action = 'delete'
            else:
                return False

            from core.utils.permission_helpers import get_anonymous_group
            anon_group = get_anonymous_group()
            if anon_group:
                # Find matching object codename via registry (section_code or fallback)
                from core.object_registry import OBJECT_REGISTRY
                for codename, obj_def in OBJECT_REGISTRY.items():
                    expected = obj_def.section_code or codename.replace('.', '_')
                    if expected == required_section:
                        perms = anon_group.object_permissions.get(codename, [])
                        if required_action in perms or 'manage' in perms:
                            return True
                        break
            return False

        # Superuser — all access
        if request.user.is_superuser:
            return True

        # Which section is required?
        required_section = getattr(view, 'required_section', None)
        if required_section is None:
            return True

        from project_customers.utils import get_customer_profile
        profile = get_customer_profile(request)
        if profile is None:
            return False

        effective = profile.get_effective_section_permissions()
        return effective.filter(code=required_section).exists()
