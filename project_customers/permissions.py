"""
project_customers/permissions.py

AccessPermission      — аутентификация по API-ключу (X-Api-Key)
SectionAccessPermission — проверка section_permissions для авторизованных пользователей
"""
import ipaddress
from datetime import date

from rest_framework.permissions import BasePermission

from project_customers.models.customer_api_key import CustomerApiKey


class AccessPermission(BasePermission):
    """
    Аутентификация по API-ключу (X-Api-Key).

    Не блокирует запросы без ключа — только добавляет request.api_key / request.customer
    при успешной проверке. Для жёсткой проверки используйте вместе с IsAuthenticated.
    """

    def has_permission(self, request, view):
        raw_key = request.headers.get('X-Api-Key', '')
        if not raw_key:
            return True

        api_key = CustomerApiKey.lookup(raw_key)
        if api_key is None:
            return True

        if api_key.access_until and api_key.access_until < date.today():
            return True

        if api_key.ip_whitelist:
            client_ip = self._get_client_ip(request)
            if not self._ip_matches(client_ip, api_key.ip_whitelist):
                return True

        request.api_key = api_key
        request.customer = api_key.customer
        return True

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')

    def _ip_matches(self, client_ip, whitelist):
        try:
            addr = ipaddress.ip_address(client_ip)
        except ValueError:
            return False
        for entry in whitelist.split(','):
            entry = entry.strip()
            if not entry:
                continue
            try:
                network = ipaddress.ip_network(entry, strict=False)
                if addr in network:
                    return True
            except ValueError:
                if entry == client_ip:
                    return True
        return False


class SectionAccessPermission(BasePermission):
    """
    Проверка прав на раздел сайта.

    Использование:
        class MyView(APIView):
            permission_classes = [SectionAccessPermission]
            required_section = 'configurator'   # ← код из SiteSection
            public = False                       # ← True = открыто для всех

    Логика:
    - public=True → доступ всем (неавторизованным тоже)
    - Неавторизованный → 401
    - Superuser → доступ
    - Иначе: проверяет section_permissions пользователя
    """

    def has_permission(self, request, view):
        # Публичные эндпоинты — открыты для всех
        if getattr(view, 'public', False):
            return True

        # Неавторизованный — отказ
        if not request.user or not request.user.is_authenticated:
            return False

        # Superuser — всё можно
        if request.user.is_superuser:
            return True

        # Какой раздел нужен?
        required_section = getattr(view, 'required_section', None)
        if required_section is None:
            return True  # Не указан — пропускаем

        # Получаем профиль клиента
        from project_customers.utils import get_customer_profile
        profile = get_customer_profile(request)
        if profile is None:
            return False

        # Проверяем права
        effective = profile.get_effective_section_permissions()
        return effective.filter(code=required_section).exists()
