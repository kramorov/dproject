from django.contrib import admin
from ..models.ai_token_usage import AITokenUsage


@admin.register(AITokenUsage)
class AITokenUsageAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "model", "prompt_tokens", "completion_tokens", "total_tokens")
