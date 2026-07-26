from django.contrib import admin
from ..models.equipment_type import EquipmentType


@admin.register(EquipmentType)
class EquipmentTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "label", "level", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("code", "label")
    list_editable = ("is_active", "level")
