"""
POST /api/auth/login/  — аутентификация (email + пароль)
POST /api/auth/logout/ — выход
GET  /api/auth/me/     — текущий пользователь (включая права anonymous_users для неавторизованных)
"""
from datetime import date

from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from project_customers.utils import get_customer_profile as _get_customer_profile


class LoginView(APIView):
    """
    Аутентификация: email + пароль.
    CustomerBackend — для клиентских пользователей (email).
    ModelBackend — для superuser/staff (username).
    """
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        csrf = request.META.get('CSRF_COOKIE', '')
        return Response({'csrftoken': csrf})

    @method_decorator(ensure_csrf_cookie)
    def post(self, request):
        login_val = request.data.get('login', '').strip()
        pwd = request.data.get('password', '')

        if not login_val or not pwd:
            return Response({'error': 'Логин и пароль обязательны'}, status=400)

        # CustomerBackend: аутентификация по login
        user = authenticate(request, login=login_val, password=pwd)
        if user is None:
            # ModelBackend: fallback — username (superuser)
            user = authenticate(request, username=login_val, password=pwd)

        if user is not None:
            login(request, user)

            if user.is_superuser:
                from project_customers.models import SiteSection
                from core.object_registry import OBJECT_REGISTRY
                return Response({
                    'system_groups': ['administrators'],
                    'object_permissions': {c: ['manage'] for c in OBJECT_REGISTRY},
                    'username': user.username,
                    'email': user.email,
                    'roles': ['admin'],
                    'section_permissions': list(
                        SiteSection.objects.filter(is_active=True).values_list('code', flat=True)
                    ),
                    'customer': '',
                })

            profile = _get_customer_profile(request)
            if profile:
                role_codes = list(profile.roles.values_list('code', flat=True))
                effective_sections = profile.get_effective_section_permissions()
                return Response({
                    'system_groups': list(profile.system_groups.values_list('code', flat=True)),
                    'object_permissions': profile.get_object_permissions(),
                    'username': profile.get_full_name(),
                    'email': profile.email,
                    'roles': role_codes,
                    'section_permissions': list(effective_sections.values_list('code', flat=True)),
                    'customer': profile.customer.name,
                })

        return Response({'error': 'Неверный email или пароль'}, status=400)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.session.pop('customer_user_id', None)
        logout(request)
        return Response({'ok': True})


class CurrentUserView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user

        # Anonymous user — return anonymous_users SystemGroup permissions
        if not user.is_authenticated:
            from core.utils.permission_helpers import get_anonymous_group
            anon_group = get_anonymous_group()
            if anon_group:
                obj_perms = anon_group.object_permissions or {}
            else:
                obj_perms = {}

            # Derive section_permissions from object codenames -> SiteSection codes
            section_codes = []
            if obj_perms:
                from project_customers.models import SiteSection
                active_sections = set(
                    SiteSection.objects.filter(is_active=True).values_list('code', flat=True)
                )
                from core.object_registry import OBJECT_REGISTRY
                for codename, actions in obj_perms.items():
                    if 'view' in actions or 'manage' in actions:
                        obj_def = OBJECT_REGISTRY.get(codename)
                        if obj_def and obj_def.section_code:
                            section_code = obj_def.section_code
                        else:
                            section_code = codename.replace('.', '_')
                        if section_code in active_sections:
                            section_codes.append(section_code)

            return Response({
                'username': '',
                'email': '',
                'roles': [],
                'section_permissions': section_codes,
                'system_groups': ['anonymous_users'],
                'object_permissions': obj_perms,
            })

        if user.is_superuser:
            from project_customers.models import SiteSection
            from core.object_registry import OBJECT_REGISTRY
            return Response({
                'system_groups': ['administrators'],
                'object_permissions': {c: ['manage'] for c in OBJECT_REGISTRY},
                'username': user.username,
                'email': user.email,
                'roles': ['admin'],
                'section_permissions': list(
                    SiteSection.objects.filter(is_active=True).values_list('code', flat=True)
                ),
                'customer': '',
            })

        profile = _get_customer_profile(request)
        if profile:
            role_codes = list(profile.roles.values_list('code', flat=True))
            effective_sections = profile.get_effective_section_permissions()
            system_groups = list(profile.system_groups.values_list('code', flat=True))
            object_perms = profile.get_object_permissions()
            return Response({
                'username': profile.get_full_name(),
                'email': profile.email,
                'roles': role_codes,
                'section_permissions': list(effective_sections.values_list('code', flat=True)),
                'customer': profile.customer.name,
                'system_groups': system_groups,
                'object_permissions': object_perms,
            })

        return Response({
            'username': user.username,
            'email': user.email,
            'roles': [],
            'section_permissions': [],
            'customer': '',
            'system_groups': [],
            'object_permissions': {},
        })
