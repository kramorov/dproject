"""
GET  /api/admin/site-sections/              — список всех SiteSection
PUT  /api/admin/site-sections/<code>/       — обновить SiteSection (is_active, name, sorting_order)

GET  /api/admin/customers/<cid>/permission-matrix/  — сводная матрица прав:
       org-level потолок + роли + пользователи + эффективные права
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Prefetch
from project_customers.permissions import SectionAccessPermission
from project_customers.models import (
    ProjectCustomer, ProjectCustomerUser, Role,
    SiteSection,
)


class SiteSectionListView(APIView):
    """Список всех SiteSection + обновление отдельного раздела."""
    permission_classes = [SectionAccessPermission]
    required_section = 'admin_section'

    def get(self, request):
        sections = SiteSection.objects.order_by('sorting_order', 'code')
        return Response({
            'sections': [
                {
                    'code': s.code,
                    'name': s.name,
                    'is_active': s.is_active,
                    'sorting_order': s.sorting_order,
                }
                for s in sections
            ]
        })

    def put(self, request, code=None):
        """Обновить один SiteSection по code."""
        if not code:
            return Response({'error': 'code required'}, status=400)
        try:
            sec = SiteSection.objects.get(code=code)
        except SiteSection.DoesNotExist:
            return Response({'error': 'Раздел не найден'}, status=404)
        for field in ('name', 'is_active', 'sorting_order'):
            if field in request.data:
                setattr(sec, field, request.data[field])
        sec.save()
        return Response({
            'code': sec.code,
            'name': sec.name,
            'is_active': sec.is_active,
            'sorting_order': sec.sorting_order,
        })


class PermissionMatrixView(APIView):
    """
    Сводная матрица прав для организации.

    Возвращает:
    - all_sections: все разделы из SiteSection (справочник)
    - org_sections: потолок прав организации (коды)
    - roles: роли организации с их section_permissions
    - users: пользователи с effective_section_permissions
    """
    permission_classes = [SectionAccessPermission]
    required_section = 'admin_section'

    def get(self, request, cid):
        try:
            customer = ProjectCustomer.objects.prefetch_related(
                'visible_sections',
                'roles__section_permissions',
                Prefetch('users', queryset=ProjectCustomerUser.objects.filter(is_active=True)),
                Prefetch('users__roles'),
                Prefetch('users__roles__section_permissions'),
                Prefetch('users__section_permissions'),
            ).get(pk=cid)
        except ProjectCustomer.DoesNotExist:
            return Response({'error': 'Клиент не найден'}, status=404)

        all_sections = list(
            SiteSection.objects.order_by('sorting_order', 'code')
            .values('code', 'name', 'is_active', 'sorting_order')
        )

        org_sections = list(
            customer.visible_sections.values_list('code', flat=True)
        )

        roles = []
        for r in customer.roles.all():
            roles.append({
                'id': r.id,
                'code': r.code,
                'name': r.name,
                'is_default': r.is_default,
                'section_permissions': list(
                    r.section_permissions.values_list('code', flat=True)
                ),
                'user_count': r.users.count(),
            })

        users = []
        for u in customer.users.all():  # уже отфильтрованы через Prefetch
            effective = u.get_effective_section_permissions()
            # Секции из ролей (без индивидуальных)
            role_section_codes = set()
            for role in u.roles.all():
                role_section_codes.update(
                    role.section_permissions.values_list('code', flat=True)
                )
            role_sections = list(role_section_codes)
            individual = list(
                u.section_permissions
                .exclude(code__in=role_section_codes)
                .values_list('code', flat=True)
            )

            users.append({
                'id': u.id,
                'name': u.get_full_name(),
                'login': u.login,
                'email': u.email,
                'is_active': u.is_active,
                'roles': list(u.roles.values_list('code', flat=True)),
                'effective_sections': list(
                    effective.values_list('code', flat=True)
                ),
                'role_sections': role_sections,
                'individual_sections': individual,
            })

        return Response({
            'customer_id': customer.id,
            'customer_name': customer.name,
            'all_sections': all_sections,
            'org_sections': org_sections,
            'roles': roles,
            'users': users,
        })
