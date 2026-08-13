"""
configurator/api/admin_serializers.py

Сериализаторы для admin CRUD endpoints.
"""
from rest_framework import serializers
from core.models import EquipmentType
from configurator.models import (
    EquipmentTypeParameter,
    ParameterRule,
    ParameterBinding,
    DerivationRule,
    FittingPattern,
    FittingPatternItem,
    ModelFieldSnapshot,
    ParameterCatalog,
)


class ParameterRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParameterRule
        fields = '__all__'


class ParameterBindingSerializer(serializers.ModelSerializer):
    equipment_type_code = serializers.SerializerMethodField()
    rule_code = serializers.SerializerMethodField()

    class Meta:
        model = ParameterBinding
        fields = '__all__'

    def get_equipment_type_code(self, obj):
        return obj.equipment_type.code if obj.equipment_type else None

    def get_rule_code(self, obj):
        return obj.rule.code if obj.rule else None


class DerivationRuleSerializer(serializers.ModelSerializer):
    source_type_code = serializers.SerializerMethodField()
    target_type_code = serializers.SerializerMethodField()

    class Meta:
        model = DerivationRule
        fields = '__all__'

    def get_source_type_code(self, obj):
        return obj.source_type.code if obj.source_type else None

    def get_target_type_code(self, obj):
        return obj.target_type.code if obj.target_type else None


class EquipmentTypeParameterSerializer(serializers.ModelSerializer):
    equipment_type_code = serializers.SerializerMethodField()
    rule_code = serializers.SerializerMethodField()

    class Meta:
        model = EquipmentTypeParameter
        fields = '__all__'

    def get_equipment_type_code(self, obj):
        return obj.equipment_type.code if obj.equipment_type else None

    def get_rule_code(self, obj):
        return obj.parameter_rule.code if obj.parameter_rule else None


class ModelFieldSnapshotSerializer(serializers.ModelSerializer):
    equipment_type_code = serializers.SerializerMethodField()

    class Meta:
        model = ModelFieldSnapshot
        fields = '__all__'

    def get_equipment_type_code(self, obj):
        return obj.equipment_type.code if obj.equipment_type else None


class ParameterCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParameterCatalog
        fields = '__all__'


class FittingPatternSerializer(serializers.ModelSerializer):
    applies_to_code = serializers.SerializerMethodField()

    class Meta:
        model = FittingPattern
        fields = '__all__'

    def get_applies_to_code(self, obj):
        return obj.applies_to.code if obj.applies_to else None


class FittingPatternItemSerializer(serializers.ModelSerializer):
    equipment_type_code = serializers.SerializerMethodField()

    class Meta:
        model = FittingPatternItem
        fields = '__all__'

    def get_equipment_type_code(self, obj):
        return obj.equipment_type.code if obj.equipment_type else None


class EquipmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentType
        fields = '__all__'
