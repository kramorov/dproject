"""
configurator/api/admin_views.py

Admin CRUD endpoints для ParameterRule, ParameterBinding,
DerivationRule, EquipmentTypeParameter.

Базовый URL: /api/configurator/admin/

Права доступа: SystemObjectPermission из core.permissions —
    superuser → всё, staff → через SystemGroup.object_permissions,
    anonymous → через anonymous_users SystemGroup.
"""
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from core.permissions import SystemObjectPermission
from configurator.models import (
    ParameterRule,
    ParameterBinding,
    DerivationRule,
    EquipmentTypeParameter,
    ModelFieldSnapshot,
    ParameterCatalog,
)
from .admin_serializers import (
    ParameterRuleSerializer,
    ParameterBindingSerializer,
    DerivationRuleSerializer,
    EquipmentTypeParameterSerializer,
    ModelFieldSnapshotSerializer,
    ParameterCatalogSerializer,
)


class ParameterRuleViewSet(viewsets.ModelViewSet):
    """CRUD для ParameterRule."""
    queryset = ParameterRule.objects.order_by('code')
    serializer_class = ParameterRuleSerializer
    permission_classes = [SystemObjectPermission]
    required_object = 'configurator.rules'
    required_action = 'edit'
    search_fields = ['code', 'name']


class ParameterBindingViewSet(viewsets.ModelViewSet):
    """CRUD для ParameterBinding."""
    queryset = ParameterBinding.objects.select_related('rule', 'equipment_type').order_by('equipment_type__code', 'param_name')
    serializer_class = ParameterBindingSerializer
    permission_classes = [SystemObjectPermission]
    required_object = 'configurator.rules'
    required_action = 'edit'
    search_fields = ['equipment_type__code', 'param_name', 'rule__code']


class DerivationRuleViewSet(viewsets.ModelViewSet):
    """CRUD для DerivationRule."""
    queryset = DerivationRule.objects.select_related('source_type', 'target_type').order_by('source_type__code', 'target_type__code')
    serializer_class = DerivationRuleSerializer
    permission_classes = [SystemObjectPermission]
    required_object = 'configurator.rules'
    required_action = 'edit'
    search_fields = ['code', 'source_type__code', 'target_type__code']


class EquipmentTypeParameterViewSet(viewsets.ModelViewSet):
    """CRUD для EquipmentTypeParameter — единая таблица параметров."""
    queryset = EquipmentTypeParameter.objects.select_related(
        'equipment_type', 'parameter_rule',
    ).order_by('equipment_type__code', 'sorting_order', 'param_name')
    serializer_class = EquipmentTypeParameterSerializer
    permission_classes = [SystemObjectPermission]
    required_object = 'configurator.rules'
    required_action = 'edit'
    search_fields = ['code', 'param_name', 'equipment_type__code', 'label']

    @action(detail=False, methods=['get'], url_path='schema')
    def schema(self, request):
        """GET /api/configurator/admin/equipment-type-parameters/schema/?equipment_type=ID"""
        et_id = request.query_params.get('equipment_type')
        if not et_id:
            return Response({'error': 'equipment_type query param required'}, status=400)
        try:
            from core.models import EquipmentType
            et = EquipmentType.objects.get(id=et_id, is_active=True)
        except EquipmentType.DoesNotExist:
            return Response({'error': f'EquipmentType id={et_id} not found'}, status=404)

        variant = request.query_params.get('variant', 'ai')
        schema = EquipmentTypeParameter.generate_json_schema(et, variant=variant)
        return Response({'equipment_type': et.code, 'name': et.name, 'variant': variant, 'schema': schema})


class ModelFieldSnapshotViewSet(viewsets.ModelViewSet):
    """CRUD для ModelFieldSnapshot — снимки полей моделей из интроспектора."""
    queryset = ModelFieldSnapshot.objects.select_related('equipment_type', 'param_name').order_by('equipment_type__code', 'depth', 'field_path')
    serializer_class = ModelFieldSnapshotSerializer
    permission_classes = [SystemObjectPermission]
    required_object = 'configurator.field_snapshots'
    required_action = 'edit'
    search_fields = ['field_path', 'param_name__code', 'equipment_type__code']
    filterset_fields = ['equipment_type', 'is_active', 'depth', 'field_type', 'param_name']


class ParameterCatalogViewSet(viewsets.ModelViewSet):
    """CRUD для ParameterCatalog — глобальный реестр канонических параметров."""
    queryset = ParameterCatalog.objects.all().order_by('namespace', 'code')
    serializer_class = ParameterCatalogSerializer
    permission_classes = [SystemObjectPermission]
    required_object = 'configurator.field_snapshots'
    required_action = 'edit'
    search_fields = ['code', 'name', 'namespace']
    filterset_fields = ['namespace', 'is_active']
