# ai_assistant/admin/admin_composition_group.py
from django.contrib import admin
from ..models.composition_group import CompositionGroup


@admin.register(CompositionGroup)
class CompositionGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "parent", "group_type", "sorting_order", "is_active")
    list_filter = ("group_type", "is_active")
    search_fields = ("name", "code", "description")
    ordering = ("sorting_order", "name")
    list_editable = ("group_type", "sorting_order", "is_active")
    raw_id_fields = ("parent",)
    filter_horizontal = ("equipment_types",)

    fieldsets = (
        (None, {
            "fields": ("name", "code", "description"),
        }),
        ("Иерархия", {
            "fields": ("parent", "group_type", "equipment_types"),
        }),
        ("Дополнительно", {
            "fields": ("sorting_order", "is_active"),
        }),
    )
