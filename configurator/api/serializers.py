"""
configurator/api/serializers.py

Сериализаторы для AssemblyRequirements и ComponentRequirement.
"""
from rest_framework import serializers

from assemblies.models import (
    AssemblyRequirements,
    ComponentRequirement,
)


class ComponentRequirementSerializer(serializers.ModelSerializer):
    """Сериализатор ComponentRequirement."""

    equipment_type_code = serializers.SerializerMethodField()
    equipment_type_name = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = ComponentRequirement
        fields = [
            'id',
            'equipment_type',
            'equipment_type_code',
            'equipment_type_name',
            'parent',
            'path',
            'level',
            'order',
            'included',
            'own_requirements',
            'effective_requirements',
            'cascade_params',
            'filter_results',
            'selected_sku',
            'selected_product_specs',
            'status',
            'composition_group_node',
            'children',
        ]
        read_only_fields = [
            'id', 'effective_requirements', 'cascade_params',
            'filter_results', 'selected_sku',
            'selected_product_specs',
            'path', 'level',
        ]

    def get_equipment_type_code(self, obj):
        return obj.equipment_type.code if obj.equipment_type else None

    def get_equipment_type_name(self, obj):
        return obj.equipment_type.name if obj.equipment_type else None

    def get_children(self, obj):
        if hasattr(obj, '_prefetched_children'):
            children = obj._prefetched_children
        else:
            children = obj.children.all()
        return ComponentRequirementSerializer(children, many=True).data


class ComponentRequirementUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления own_requirements."""

    class Meta:
        model = ComponentRequirement
        fields = ['own_requirements', 'status', 'included', 'selected_sku']


class AssemblyRequirementsSerializer(serializers.ModelSerializer):
    """Сериализатор AssemblyRequirements с деревом компонентов."""

    composition_group_code = serializers.SerializerMethodField()
    components = serializers.SerializerMethodField()

    class Meta:
        model = AssemblyRequirements
        fields = [
            'id',
            'name',
            'composition_group',
            'composition_group_code',
            'global_requirements',
            'status',
            'revision',
            'parent_assembly',
            'is_template',
            'requirement_version',
            'fixed_at',
            'fixation_comment',
            'created_at',
            'updated_at',
            'components',
        ]
        read_only_fields = [
            'id', 'revision', 'parent_assembly',
            'fixed_at', 'created_at', 'updated_at',
        ]

    def get_composition_group_code(self, obj):
        return obj.composition_group.code if obj.composition_group else None

    def get_components(self, obj):
        roots = obj.components.filter(parent__isnull=True).order_by('order')
        return ComponentRequirementSerializer(roots, many=True).data


class AssemblyRequirementsCreateSerializer(serializers.Serializer):
    """Сериализатор для создания AssemblyRequirements."""

    composition_group_id = serializers.IntegerField()
    name = serializers.CharField(required=False, allow_blank=True, default='')
    global_requirements = serializers.JSONField(required=False, default=dict)

    def validate_composition_group_id(self, value):
        from ai_assistant.models import CompositionGroup
        if not CompositionGroup.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError(f"CompositionGroup id={value} not found or inactive")
        return value
