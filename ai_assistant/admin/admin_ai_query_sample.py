from django.contrib import admin
from ..models.ai_query_sample import AIQuerySample


@admin.register(AIQuerySample)
class AIQuerySampleAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "expected_intent", "is_valid", "created_at")
    list_filter = ("category", "is_valid", "expected_intent")
    search_fields = ("text",)
    list_editable = ("is_valid", "category", "expected_intent")
