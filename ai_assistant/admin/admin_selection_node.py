from django.contrib import admin
from ..models.selection_node import SelectionNode


@admin.register(SelectionNode)
class SelectionNodeAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "level", "equipment_type", "task_type", "status", "quantity", "created_at")
    list_filter = ("status", "task_type", "level", "equipment_type")
    search_fields = ("label", "path", "conversation__id")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("conversation", "parent", "equipment_type")
