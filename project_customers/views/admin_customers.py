"""
GET  /api/admin/customers/         — список всех клиентов
GET  /api/admin/customers/<id>/    — клиент + пользователи + роли + ключи + доступ
POST /api/admin/customers/<id>/    — обновить клиента и все вложенные данные
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from project_customers.permissions import SectionAccessPermission
from project_customers.models import (
    ProjectCustomer, ProjectCustomerUser, Role, CustomerApiKey,
    CustomerAppAccess, CustomerEmail, SiteSection, AllowedApp,
)


class CustomerAdminView(APIView):
    permission_classes = [SectionAccessPermission]
    required_section = 'admin_section'

    def get(self, request, pk=None):
        if pk:
            return self._get_detail(pk)
        return self._get_list()

    def _get_list(self):
        customers = ProjectCustomer.objects.prefetch_related(
            'users', 'api_keys', 'roles'
        ).order_by('name')
        data = [{
            'id': c.id,
            'name': c.name,
            'short_name': c.short_name,
            'is_active': c.is_active,
            'access_until': c.access_until,
            'email': c.email,
            'phone': c.phone,
            'users_count': c.users.count(),
            'api_keys_count': c.api_keys.filter(is_active=True).count(),
        } for c in customers]
        return Response({'customers': data})

    def _get_detail(self, pk):
        try:
            c = ProjectCustomer.objects.prefetch_related(
                'users__roles', 'users__section_permissions',
                'roles__section_permissions', 'roles__django_user',
                'api_keys__allowed_apps',
                'app_access__app', 'app_access__brands',
                'notification_emails',
                'visible_sections', 'visible_brands',
            ).get(pk=pk)
        except ProjectCustomer.DoesNotExist:
            return Response({'error': 'Клиент не найден'}, status=404)

        data = {
            'id': c.id,
            'name': c.name,
            'short_name': c.short_name,
            'is_active': c.is_active,
            'access_until': c.access_until,
            'email': c.email,
            'phone': c.phone,
            'visible_sections': list(c.visible_sections.values_list('code', flat=True)),
            'visible_brands': [{'id': b.id, 'name': b.name} for b in c.visible_brands.all()],
            'users': [{
                'id': u.id,
                'first_name': u.first_name, 'last_name': u.last_name,
                'email': u.email, 'phone': u.phone, 'position': u.position,
                'is_active': u.is_active,
                'roles': list(u.roles.values_list('code', flat=True)),
                'section_permissions': list(u.section_permissions.values_list('code', flat=True)),
            } for u in c.users.all()],
            'roles': [{
                'id': r.id, 'code': r.code, 'name': r.name,
                'is_default': r.is_default,
                'django_user': r.django_user.username if r.django_user else None,
                'section_permissions': list(r.section_permissions.values_list('code', flat=True)),
            } for r in c.roles.all()],
            'api_keys': [{
                'id': k.id, 'name': k.name, 'key_prefix': k.key_prefix,
                'is_active': k.is_active, 'access_until': k.access_until,
                'last_used_at': k.last_used_at, 'created_at': k.created_at,
                'allowed_apps': list(k.allowed_apps.values_list('code', flat=True)),
                'ip_whitelist': k.ip_whitelist, 'llm_endpoint': k.llm_endpoint,
            } for k in c.api_keys.all()],
            'app_access': [{
                'app_code': a.app.code, 'app_name': a.app.name,
                'brand_filter': a.brand_filter, 'is_active': a.is_active,
                'brands': list(a.brands.values_list('id', flat=True)),
            } for a in c.app_access.all()],
            'notification_emails': [{
                'id': e.id, 'email_type': e.email_type, 'email': e.email, 'is_active': e.is_active,
            } for e in c.notification_emails.all()],
        }
        return Response(data)

    def post(self, request, pk=None):
        data = request.data
        if pk:
            return self._update_customer(pk, data)
        return self._create_customer(data)

    def _create_customer(self, data):
        name = data.get('name', '').strip()
        if not name:
            return Response({'error': 'Название обязательно'}, status=400)
        c = ProjectCustomer.objects.create(
            name=name,
            short_name=data.get('short_name', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            is_active=data.get('is_active', True),
            access_until=data.get('access_until') or None,
        )
        return Response({'id': c.id, 'name': c.name}, status=201)

    def _update_customer(self, pk, data):
        try:
            c = ProjectCustomer.objects.get(pk=pk)
        except ProjectCustomer.DoesNotExist:
            return Response({'error': 'Клиент не найден'}, status=404)

        for field in ['name', 'short_name', 'email', 'phone', 'is_active']:
            if field in data:
                setattr(c, field, data[field])
        if 'access_until' in data:
            c.access_until = data['access_until'] or None
        c.save()

        # visible_sections
        if 'visible_sections' in data:
            c.visible_sections.set(
                SiteSection.objects.filter(code__in=data['visible_sections'])
            )

        # roles
        if 'roles' in data:
            existing_role_ids = set(c.roles.values_list('id', flat=True))
            for r_data in data['roles']:
                if r_data.get('id') and r_data['id'] in existing_role_ids:
                    role = c.roles.get(id=r_data['id'])
                    role.name = r_data.get('name', role.name)
                    role.is_default = r_data.get('is_default', role.is_default)
                    role.save()
                    if 'section_permissions' in r_data:
                        role.section_permissions.set(
                            SiteSection.objects.filter(code__in=r_data['section_permissions'])
                        )
                elif not r_data.get('id'):
                    role = Role.objects.create(
                        customer=c, code=r_data.get('code', ''), name=r_data.get('name', ''),
                    )
                    if 'section_permissions' in r_data:
                        role.section_permissions.set(
                            SiteSection.objects.filter(code__in=r_data['section_permissions'])
                        )

        # api_keys
        if 'api_keys' in data:
            existing_key_ids = set(c.api_keys.values_list('id', flat=True))
            for k_data in data['api_keys']:
                if k_data.get('id') and k_data['id'] in existing_key_ids:
                    key = c.api_keys.get(id=k_data['id'])
                    key.is_active = k_data.get('is_active', key.is_active)
                    if 'access_until' in k_data:
                        key.access_until = k_data['access_until'] or None
                    key.save()
                    if 'allowed_apps' in k_data:
                        key.allowed_apps.set(
                            AllowedApp.objects.filter(code__in=k_data['allowed_apps'])
                        )

        # app_access
        if 'app_access' in data:
            for a_data in data['app_access']:
                app = AllowedApp.objects.filter(code=a_data['app_code']).first()
                if app:
                    access, _ = CustomerAppAccess.objects.get_or_create(
                        customer=c, app=app,
                        defaults={'brand_filter': a_data.get('brand_filter', 'all'), 'is_active': True}
                    )
                    access.brand_filter = a_data.get('brand_filter', access.brand_filter)
                    access.is_active = a_data.get('is_active', True)
                    access.save()
                    if 'brands' in a_data:
                        access.brands.set(a_data['brands'])

        return self._get_detail(pk)

    def delete(self, request, pk=None):
        if not pk:
            return Response({'error': 'ID обязателен'}, status=400)
        try:
            c = ProjectCustomer.objects.get(pk=pk)
            c.is_active = False
            c.save()
            return Response({'ok': True})
        except ProjectCustomer.DoesNotExist:
            return Response({'error': 'Клиент не найден'}, status=404)


class CustomerUserAdminView(APIView):
    permission_classes = [SectionAccessPermission]
    required_section = 'admin_section'

    def post(self, request, cid):
        try:
            c = ProjectCustomer.objects.get(pk=cid)
        except ProjectCustomer.DoesNotExist:
            return Response({'error': 'Клиент не найден'}, status=404)
        login_val = request.data.get('login', '').strip()
        if not login_val:
            return Response({'error': 'Логин обязателен'}, status=400)
        user = ProjectCustomerUser.objects.create(
            customer=c, login=login_val,
            first_name=request.data.get('first_name', ''),
            last_name=request.data.get('last_name', ''),
            email=request.data.get('email', ''),
            phone=request.data.get('phone', ''),
            position=request.data.get('position', ''),
            is_active=request.data.get('is_active', True),
        )
        pwd = request.data.get('password', '')
        if pwd:
            user.set_password(pwd)
        role_codes = request.data.get('roles', [])
        if role_codes:
            user.roles.set(Role.objects.filter(customer=c, code__in=role_codes))
        user.save()
        return Response({'id': user.id, 'login': user.login}, status=201)

    def put(self, request, cid):
        uid = request.data.get('id')
        if not uid:
            return Response({'error': 'ID обязателен'}, status=400)
        try:
            user = ProjectCustomerUser.objects.get(pk=uid, customer_id=cid)
        except ProjectCustomerUser.DoesNotExist:
            return Response({'error': 'Не найден'}, status=404)
        for field in ['login', 'first_name', 'last_name', 'email', 'phone', 'position', 'is_active']:
            if field in request.data:
                setattr(user, field, request.data[field])
        pwd = request.data.get('password', '')
        if pwd:
            user.set_password(pwd)
        if 'roles' in request.data:
            user.roles.set(Role.objects.filter(customer_id=cid, code__in=request.data['roles']))
        user.save()
        return Response({'ok': True})

    def delete(self, request, cid):
        uid = request.data.get('id')
        if not uid:
            return Response({'error': 'ID обязателен'}, status=400)
        ProjectCustomerUser.objects.filter(pk=uid, customer_id=cid).delete()
        return Response({'ok': True})


class CustomerKeyAdminView(APIView):
    permission_classes = [SectionAccessPermission]
    required_section = 'admin_section'

    def post(self, request, cid):
        try:
            c = ProjectCustomer.objects.get(pk=cid)
        except ProjectCustomer.DoesNotExist:
            return Response({'error': 'Клиент не найден'}, status=404)
        name = request.data.get('name', '').strip()
        if not name:
            return Response({'error': 'Название обязательно'}, status=400)
        instance, raw_key = CustomerApiKey.generate_key(customer=c, name=name)
        allowed_apps = request.data.get('allowed_apps', [])
        if allowed_apps:
            instance.allowed_apps.set(AllowedApp.objects.filter(code__in=allowed_apps))
        for field in ['ip_whitelist', 'access_until', 'llm_endpoint']:
            if field in request.data:
                setattr(instance, field, request.data[field])
        instance.save()
        return Response({
            'id': instance.id, 'name': instance.name,
            'key_prefix': instance.key_prefix, 'raw_key': raw_key,
            'warning': 'Сохраните raw_key — он больше не будет показан.',
        }, status=201)

    def delete(self, request, cid):
        kid = request.data.get('id')
        if not kid:
            return Response({'error': 'ID ключа обязателен'}, status=400)
        CustomerApiKey.objects.filter(pk=kid, customer_id=cid).update(is_active=False)
        return Response({'ok': True})
