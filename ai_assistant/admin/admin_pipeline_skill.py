from django.contrib import admin
from ..models.pipeline_skill import PipelineSkill


@admin.register(PipelineSkill)
class PipelineSkillAdmin(admin.ModelAdmin):
    list_display = ("code", "step", "equipment_type", "prompt_template", "model_role", "priority", "is_active")
    list_filter = ("step", "is_active", "model_role")
    search_fields = ("code", "step")
    list_editable = ("is_active", "priority", "model_role")
    autocomplete_fields = ("equipment_type", "prompt_template", "output_schema")
