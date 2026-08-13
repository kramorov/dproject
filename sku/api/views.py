from rest_framework import viewsets

from core.permissions import SystemObjectPermission
from sku.models import SKU
from .serializers import SKUSerializer


class SKUViewSet(viewsets.ModelViewSet):
    """Полный CRUD для SKU (номенклатура)."""
    queryset = SKU.objects.select_related('equipment_type', 'brand').order_by('code')
    serializer_class = SKUSerializer
    permission_classes = [SystemObjectPermission]
    required_object = 'sku.admin'
    required_action = 'edit'
    search_fields = ['code', 'name']
    filterset_fields = ['equipment_type', 'brand', 'is_active']
