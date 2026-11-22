# valve_data/admin/admin_torque_characteristics.py
from django.contrib import admin

from valve_data.models import (
    SealType,
    TorquePoint,
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


@admin.register(TorquePoint)
class TorquePointAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'direction', 'position', 'sorting_order', 'is_active')
    list_editable = ('sorting_order', 'is_active')
    list_filter = ('direction', 'position', 'is_active')
    search_fields = ('code', 'name')
    ordering = ('sorting_order', 'id')


@admin.register(TorqueThrustCharacteristics)
class TorqueThrustCharacteristicsAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'motion_type', 'sorting_order', 'is_active')
    list_filter = ('motion_type', 'is_active')
    filter_horizontal = ('points',)
    search_fields = ('code', 'name')
    ordering = ('sorting_order', 'id')


@admin.register(ValveTorqueCoefficient)
class ValveTorqueCoefficientAdmin(admin.ModelAdmin):
    list_display = ('characteristics', 'valve_type', 'support', 'seal_type', 'point',
                    'factor', 'min_factor', 'display', 'is_active')
    list_filter = ('characteristics', 'valve_type', 'seal_type', 'point', 'is_active')
    search_fields = ('characteristics__code', 'valve_type__code', 'point__code')
    ordering = ('characteristics', 'valve_type', 'point__sorting_order', 'id')
