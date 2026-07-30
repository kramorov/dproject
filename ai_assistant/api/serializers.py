from rest_framework import serializers

from ..models import (
    AIConversation, AIMessage, AITokenUsage,
    AIClientProvider, AIQuerySample, AIPromptTemplate,
    PipelineSkill, SkillOverride, JSONSchema, CompositionGroup,
)
from core.models import EquipmentType
from sku.models import MBOM, MBOMItem


class AIConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIConversation
        fields = "__all__"


class AIMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIMessage
        fields = "__all__"


class AITokenUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AITokenUsage
        fields = "__all__"


class AIQuerySampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIQuerySample
        fields = "__all__"


class AIPromptTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIPromptTemplate
        fields = "__all__"


class PipelineSkillSerializer(serializers.ModelSerializer):
    equipment_type_detail = serializers.SerializerMethodField()
    prompt_template_detail = serializers.SerializerMethodField()

    class Meta:
        model = PipelineSkill
        fields = "__all__"

    def get_equipment_type_detail(self, obj):
        if obj.equipment_type:
            return {"id": obj.equipment_type.id, "name": obj.equipment_type.name, "code": obj.equipment_type.code}
        return None

    def get_prompt_template_detail(self, obj):
        if obj.prompt_template:
            return {"id": obj.prompt_template.id, "code": obj.prompt_template.code, "name": obj.prompt_template.name}
        return None


class SkillOverrideSerializer(serializers.ModelSerializer):
    step_config_detail = serializers.SerializerMethodField()
    customer_detail = serializers.SerializerMethodField()

    class Meta:
        model = SkillOverride
        fields = "__all__"

    def get_step_config_detail(self, obj):
        if obj.step_config:
            return {"id": obj.step_config.id, "code": obj.step_config.code, "step": obj.step_config.step}
        return None

    def get_customer_detail(self, obj):
        if obj.customer_id:
            from project_customers.models import ProjectCustomer
            try:
                c = ProjectCustomer.objects.get(id=obj.customer_id)
                return {"id": c.id, "name": c.name}
            except ProjectCustomer.DoesNotExist:
                pass
        return None


class JSONSchemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = JSONSchema
        fields = "__all__"


class QueryRequestSerializer(serializers.Serializer):
    text = serializers.CharField(required=True, max_length=4096)
    session_key = serializers.CharField(required=False, max_length=64)
    customer_id = serializers.IntegerField(required=False)


class QueryResponseSerializer(serializers.Serializer):
    conversation_id = serializers.IntegerField()
    intent = serializers.CharField()
    confidence = serializers.FloatField(required=False)
    filters = serializers.JSONField(required=False, allow_null=True)
    search_results = serializers.JSONField(required=False)
    total_tokens = serializers.IntegerField(required=False)
    total_cost = serializers.FloatField(required=False)
    latency_ms = serializers.IntegerField(required=False)
    reply_text = serializers.CharField()


# ── CompositionGroup ──

class CompositionGroupSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    equipment_types_detail = serializers.SerializerMethodField()

    class Meta:
        model = CompositionGroup
        fields = [
            "id", "name", "code", "description", "parent",
            "group_type", "sorting_order", "is_active",
            "equipment_types", "equipment_types_detail",
            "children", "created_at", "updated_at",
        ]

    def get_children(self, obj):
        children = obj.children.filter(is_active=True).order_by("sorting_order", "name")
        return CompositionGroupSerializer(children, many=True).data

    def get_equipment_types_detail(self, obj):
        return [
            {"id": et.id, "code": et.code, "name": et.name, "level": et.level}
            for et in obj.equipment_types.filter(is_active=True)
        ]


# ── CompositionGroup tree (lightweight) ──

class CompositionGroupTreeSerializer(serializers.ModelSerializer):
    """Лёгкий сериализатор для дерева CompositionGroup + EquipmentType."""
    children = serializers.SerializerMethodField()
    item_type = serializers.SerializerMethodField()

    class Meta:
        model = CompositionGroup
        fields = ["id", "name", "code", "group_type", "item_type", "children"]

    def get_item_type(self, obj):
        return "composition_group"

    def get_children(self, obj):
        et_nodes = EquipmentTypeTreeSerializer(
            obj.equipment_types.filter(is_active=True).order_by("name"),
            many=True,
        ).data
        # Inject item_type for frontend
        for node in et_nodes:
            node["item_type"] = "equipment_type"
        # Child composition groups
        cg_nodes = []
        for child in obj.children.filter(is_active=True).order_by("sorting_order", "name"):
            cg_nodes.append(CompositionGroupTreeSerializer(child).data)
        return et_nodes + cg_nodes


# ── EquipmentType tree (for drag-drop source) ──

class EquipmentTypeTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = EquipmentType
        fields = ["id", "name", "code", "level", "icon", "children"]

    def get_children(self, obj):
        children = obj.children.filter(is_active=True).order_by("sorting_order", "name")
        return EquipmentTypeTreeSerializer(children, many=True).data


# ── MBOM ──

class MBOMItemSerializer(serializers.ModelSerializer):
    equipment_type_name = serializers.SerializerMethodField()
    sku_code = serializers.SerializerMethodField()
    sku_name = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = MBOMItem
        fields = [
            "id", "mbom", "parent", "equipment_type", "equipment_type_name",
            "composition_group", "sku", "sku_code", "sku_name",
            "quantity", "quantity_unit", "position", "notes", "children",
        ]

    def get_equipment_type_name(self, obj):
        return obj.equipment_type.name if obj.equipment_type else None

    def get_sku_code(self, obj):
        return obj.sku.code if obj.sku else None

    def get_sku_name(self, obj):
        return obj.sku.name if obj.sku else None

    def get_children(self, obj):
        children = obj.children.all().order_by("position")
        return MBOMItemSerializer(children, many=True).data


class MBOMSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = MBOM
        fields = [
            "id", "name", "code", "description", "conversation",
            "customer", "customer_name", "user", "user_name",
            "is_active", "created_at", "updated_at", "items",
        ]
        read_only_fields = ["customer", "user"]

    def get_customer_name(self, obj):
        return obj.customer.name if obj.customer else None

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username if obj.user else None

    def get_items(self, obj):
        root_items = obj.items.filter(parent__isnull=True).order_by("position")
        return MBOMItemSerializer(root_items, many=True).data
