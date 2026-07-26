from django.contrib import admin
from ..models.ai_provider import AIProvider


@admin.register(AIProvider)
class AIProviderAdmin(admin.ModelAdmin):
    list_display = ("code", "is_active", "base_url")
    list_editable = ("is_active",)
    search_fields = ("code",)
