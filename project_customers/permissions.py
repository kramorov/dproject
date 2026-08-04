"""
project_customers/permissions.py

AccessPermission      — API-key auth (X-Api-Key)
SectionAccessPermission — re-export of core.permissions.OrgSectionPermission
"""
import ipaddress
from datetime import date

from rest_framework.permissions import BasePermission
from core.permissions import OrgSectionPermission as SectionAccessPermission  # noqa: F401

from project_customers.models.customer_api_key import CustomerApiKey


class AccessPermission(BasePermission):
    """
    API-key authentication (X-Api-Key).

    Does NOT block requests without a key — only adds request.api_key / request.customer
    on success. Use with IsAuthenticated for hard enforcement.
    """

    def has_permission(self, request, view):
        raw_key = request.headers.get('X-Api-Key', '')
        if not raw_key:
            return True

        api_key= [redacted]
        if api_key is None:
            return True

        if api_key.access_until and api_key.access_until < date.today():
            return True

        if api_key.ip_whitelist:
            client_ip = self._get_client_ip(request)
            if not self._ip_matches(client_ip, api_key.ip_whitelist):
                return True

        request.api_key= [redacted]
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
