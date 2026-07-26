from django.contrib import admin
from ..models.ai_message import AIMessage


@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "role", "intent", "confidence", "is_error", "created_at")
    list_filter = ("role", "intent", "is_error")
    search_fields = ("content", "error_message")
    readonly_fields = ("created_at",)
