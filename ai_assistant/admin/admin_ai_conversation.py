from django.contrib import admin
from ..models.ai_conversation import AIConversation


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "status", "intent", "source", "created_at")
    list_filter = ("status", "source", "intent")
    search_fields = ("session_key",)
    readonly_fields = ("created_at", "updated_at")
