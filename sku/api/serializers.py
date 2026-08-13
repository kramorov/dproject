from rest_framework import serializers

from sku.models import SKU


class SKUSerializer(serializers.ModelSerializer):
    equipment_type_code = serializers.SerializerMethodField()
    brand_name = serializers.SerializerMethodField()

    class Meta:
        model = SKU
        fields = '__all__'

    def get_equipment_type_code(self, obj):
        return obj.equipment_type.code if obj.equipment_type else None

    def get_brand_name(self, obj):
        return obj.brand.name if obj.brand else None
