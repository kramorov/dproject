from django.contrib import admin
from ..models.ai_token_usage import AITokenUsage


@admin.register(AITokenUsage)
class AITokenUsageAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "customer", "model", "prompt_tokens", "completion_tokens", "total_tokens", "latency_ms")
    list_filter = ("model",)
    search_fields = ("message__content", "customer__name")
