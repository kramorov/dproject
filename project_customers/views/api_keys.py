"""
GET    /api/auth/api-keys/      — список ключей клиента
POST   /api/auth/api-keys/      — создать новый ключ
DELETE /api/auth/api-keys/<id>/  — отозвать ключ
"""
from datetime import date

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from project_customers.models.customer_api_key import CustomerApiKey
from project_customers.models.user import ProjectCustomerUser
from project_customers.utils import get_customer_profile as _get_customer_profile


class ApiKeyListView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_customer(self, request):
        if request.user.is_superuser:
            return None
        profile = _get_customer_profile(request)
        if profile is None:
            return False
        customer = profile.customer
        if not customer.is_active:
            return False
        if customer.access_until and customer.access_until < date.today():
            return False
        return customer

    def get(self, request):
        customer = self._get_customer(request)
        if customer is False:
            return Response({'error': 'Доступ запрещён'}, status=403)

        qs = CustomerApiKey.objects.all()
        if customer is not None:
            qs = qs.filter(customer=customer)

        keys = [{
            'id': k.id,
            'name': k.name,
            'key_prefix': k.key_prefix,
            'is_active': k.is_active,
            'access_until': k.access_until,
            'last_used_at': k.last_used_at,
            'created_at': k.created_at,
            'allowed_apps': list(k.allowed_apps.values_list('code', flat=True)),
        } for k in qs.order_by('-created_at')]

        return Response({'keys': keys})

    def post(self, request):
        customer = self._get_customer(request)
        if customer is False:
            return Response({'error': 'Доступ запрещён'}, status=403)
        if customer is None:
            return Response({'error': 'Суперюзер должен указать customer_id'}, status=400)

        name = request.data.get('name', '').strip()
        if not name:
            return Response({'error': 'Название ключа обязательно'}, status=400)

        instance, raw_key = CustomerApiKey.generate_key(customer=customer, name=name)

        allowed_app_codes = request.data.get('allowed_apps', [])
        if allowed_app_codes:
            from project_customers.models import AllowedApp
            apps = AllowedApp.objects.filter(code__in=allowed_app_codes)
            instance.allowed_apps.set(apps)

        for field in ['brand_filters', 'ip_whitelist', 'access_until', 'llm_endpoint']:
            val = request.data.get(field)
            if val:
                setattr(instance, field, val)

        instance.save()

        return Response({
            'id': instance.id,
            'name': instance.name,
            'key_prefix': instance.key_prefix,
            'raw_key': raw_key,
            'is_active': instance.is_active,
            'created_at': instance.created_at,
            'allowed_apps': list(instance.allowed_apps.values_list('code', flat=True)),
            'warning': 'Сохраните raw_key — он больше не будет показан.',
        }, status=status.HTTP_201_CREATED)


class ApiKeyDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_customer(self, request):
        if request.user.is_superuser:
            return None
        profile = _get_customer_profile(request)
        if profile is None:
            return False
        return profile.customer

    def delete(self, request, pk):
        customer = self._get_customer(request)
        if customer is False:
            return Response({'error': 'Доступ запрещён'}, status=403)

        try:
            key = CustomerApiKey.objects.get(pk=pk)
        except CustomerApiKey.DoesNotExist:
            return Response({'error': 'Ключ не найден'}, status=404)

        if customer is not None and key.customer_id != customer.id:
            return Response({'error': 'Доступ запрещён'}, status=403)

        key.is_active = False
        key.save(update_fields=['is_active'])

        return Response({
            'id': key.id,
            'name': key.name,
            'is_active': False,
            'message': 'Ключ отозван',
        })
