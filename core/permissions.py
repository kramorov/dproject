"""
core/permissions.py — DRF permission classes.

SystemObjectPermission  — system-level: checks group object_permissions
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

        # Not authenticated
        if not request.user or not request.user.is_authenticated:
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
