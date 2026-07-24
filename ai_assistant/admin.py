from django.contrib import admin
from .models import (
    AIConversation, AIMessage, AITokenUsage,
    AIClientProvider, AIQuerySample, AIPromptTemplate, AIProvider,
)


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "status", "intent", "source", "created_at")
    list_filter = ("status", "source", "intent")
    search_fields = ("session_key",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "role", "intent", "confidence", "is_error", "created_at")
    list_filter = ("role", "intent", "is_error")
    search_fields = ("content", "error_message")
    readonly_fields = ("created_at",)


@admin.register(AITokenUsage)
class AITokenUsageAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "model", "prompt_tokens", "completion_tokens", "total_tokens")


@admin.register(AIClientProvider)
class AIClientProviderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "provider_type", "is_active")


@admin.register(AIQuerySample)
class AIQuerySampleAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "expected_intent", "is_valid", "created_at")
    list_filter = ("category", "is_valid", "expected_intent")
    search_fields = ("text",)
    list_editable = ("is_valid", "category", "expected_intent")


@admin.register(AIPromptTemplate)
class AIPromptTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "version", "intent", "is_active")
    list_filter = ("is_active", "intent")
    search_fields = ("name", "template_text")
    list_editable = ("is_active",)


@admin.register(AIProvider)
class AIProviderAdmin(admin.ModelAdmin):
    list_display = ("code", "is_active", "base_url")
    list_editable = ("is_active",)
    search_fields = ("code",)
