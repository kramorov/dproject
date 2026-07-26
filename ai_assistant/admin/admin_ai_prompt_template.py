from django.contrib import admin
from ..models.ai_prompt_template import AIPromptTemplate


@admin.register(AIPromptTemplate)
class AIPromptTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "version", "intent", "is_active")
    list_filter = ("is_active", "intent")
    search_fields = ("name", "template_text")
    list_editable = ("is_active",)
