from django.contrib import admin
from ..models.ai_client_provider import AIClientProvider


@admin.register(AIClientProvider)
class AIClientProviderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "provider_type", "is_active")
