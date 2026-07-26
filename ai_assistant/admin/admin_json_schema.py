from django.contrib import admin
from ..models.json_schema import JSONSchema


@admin.register(JSONSchema)
class JSONSchemaAdmin(admin.ModelAdmin):
    list_display = ("name", "version", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    list_editable = ("is_active",)
