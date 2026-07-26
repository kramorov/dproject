from django.contrib import admin
from ..models.step_config_override import StepConfigOverride


@admin.register(StepConfigOverride)
class StepConfigOverrideAdmin(admin.ModelAdmin):
    list_display = ("customer", "step_config", "model_role", "is_active")
    list_filter = ("is_active",)
    search_fields = ("customer__name",)
    list_editable = ("is_active", "model_role")
    autocomplete_fields = ("customer", "step_config", "prompt_template", "output_schema")
