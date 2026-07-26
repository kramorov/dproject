from django.contrib import admin
from ..models.step_config import StepConfig


@admin.register(StepConfig)
class StepConfigAdmin(admin.ModelAdmin):
    list_display = ("step", "equipment_type", "prompt_template", "model_role", "priority", "is_active")
    list_filter = ("step", "is_active", "model_role")
    search_fields = ("step",)
    list_editable = ("is_active", "priority", "model_role")
    autocomplete_fields = ("equipment_type", "prompt_template", "output_schema")
