"""
configurator/api/admin_serializers.py

Сериализаторы для admin CRUD endpoints.
"""
from rest_framework import serializers
from configurator.models import (
    EquipmentTypeParameter,
    PropagationRule,
    ParameterRule,
    ParameterBinding,
    DerivationRule,
)


class PropagationRuleSerializer(serializers.ModelSerializer):
    equipment_type_code = serializers.SerializerMethodField()

    class Meta:
        model = PropagationRule
        fields = '__all__'

    def get_equipment_type_code(self, obj):
        return obj.equipment_type.code if obj.equipment_type else None


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
