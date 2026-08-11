"""
configurator/api/admin_views.py

Admin CRUD endpoints для PropagationRule, ParameterRule, ParameterBinding, DerivationRule.

Базовый URL: /api/configurator/admin/
"""
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from configurator.models import (
    PropagationRule,
    ParameterRule,
    ParameterBinding,
    DerivationRule,
    EquipmentTypeParameter,
)
from .admin_serializers import (
    PropagationRuleSerializer,
    ParameterRuleSerializer,
    ParameterBindingSerializer,
    DerivationRuleSerializer,
    EquipmentTypeParameterSerializer,
)


class PropagationRuleViewSet(viewsets.ModelViewSet):
    """CRUD для PropagationRule."""
    queryset = PropagationRule.objects.select_related('equipment_type').order_by('equipment_type__code', 'param_name')
    serializer_class = PropagationRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['code', 'param_name', 'equipment_type__code']


class ParameterRuleViewSet(viewsets.ModelViewSet):
    """CRUD для ParameterRule."""
    queryset = ParameterRule.objects.order_by('code')
    serializer_class = ParameterRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['code', 'name']


class ParameterBindingViewSet(viewsets.ModelViewSet):
    """CRUD для ParameterBinding."""
    queryset = ParameterBinding.objects.select_related('rule', 'equipment_type').order_by('equipment_type__code', 'param_name')
    serializer_class = ParameterBindingSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['equipment_type__code', 'param_name', 'rule__code']


class DerivationRuleViewSet(viewsets.ModelViewSet):
    """CRUD для DerivationRule."""
    queryset = DerivationRule.objects.select_related('source_type', 'target_type').order_by('source_type__code', 'target_type__code')
    serializer_class = DerivationRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['code', 'source_type__code', 'target_type__code']


class EquipmentTypeParameterViewSet(viewsets.ModelViewSet):
    """CRUD для EquipmentTypeParameter — единая таблица параметров."""
    queryset = EquipmentTypeParameter.objects.select_related(
        'equipment_type', 'parameter_rule',
    ).order_by('equipment_type__code', 'sorting_order', 'param_name')
    serializer_class = EquipmentTypeParameterSerializer
    permission_classes = [permissions.IsAuthenticated]
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
