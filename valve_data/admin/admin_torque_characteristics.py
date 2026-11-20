# valve_data/admin/admin_torque_characteristics.py
from django.contrib import admin

from valve_data.models import (
    SealType,
    TorqueThrustCharacteristics,
    ValveSupportType,
    ValveTorqueCoefficient,
)


@admin.register(SealType)
class SealTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'sorting_order', 'is_active')
    list_editable = ('sorting_order', 'is_active')
    search_fields = ('code', 'name')
    ordering = ('sorting_order', 'id')


@admin.register(ValveSupportType)
class ValveSupportTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'sorting_order', 'is_active')
    list_editable = ('sorting_order', 'is_active')
    search_fields = ('code', 'name')
    ordering = ('sorting_order', 'id')


@admin.register(TorqueThrustCharacteristics)
class TorqueThrustCharacteristicsAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'motion_type', 'sorting_order', 'is_active')
    list_filter = ('motion_type', 'is_active')
    search_fields = ('code', 'name')
    ordering = ('sorting_order', 'id')


@admin.register(ValveTorqueCoefficient)
class ValveTorqueCoefficientAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'characteristics', 'valve_type', 'support', 'seal_type', 'is_active')
    list_filter = ('characteristics', 'valve_type', 'seal_type', 'is_active')
    search_fields = ('code', 'name')
    ordering = ('characteristics', 'sorting_order', 'id')
