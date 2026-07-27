from rest_framework import serializers

from ..models import (
    AIConversation, AIMessage, AITokenUsage,
    AIClientProvider, AIQuerySample, AIPromptTemplate,
    PipelineSkill, SkillOverride, JSONSchema,
)


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
