from django.contrib import admin
from ..models.cascade_rule import CascadeRule


@admin.register(CascadeRule)
class CascadeRuleAdmin(admin.ModelAdmin):
    list_display = ("parent_type", "child_type", "is_active")
    list_filter = ("is_active",)
    search_fields = ("parent_type__code", "child_type__code")
    list_editable = ("is_active",)
    autocomplete_fields = ("parent_type", "child_type")
