from rest_framework import serializers

from ..models import (
    AIConversation, AIMessage, AITokenUsage,
    AIClientProvider, AIQuerySample, AIPromptTemplate,
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
