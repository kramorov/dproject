# solenoid_valves/admin/sv_options_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.models.mixins import AdminStructuredDataMixinCopyMixin
from solenoid_valves.models import (
    ValveDesign, ValveOperationVariety, ValveFunction,
    ValveActuationVariety, ManualOverride, ValvePilotVariety,
)


@admin.register(ValveDesign)
class ValveDesignAdmin(AdminStructuredDataMixinCopyMixin, admin.ModelAdmin):
    list_display = ('name', 'code', 'sorting_order', 'is_active')
    list_editable = ('sorting_order', 'is_active')
    search_fields = ('name', 'code')
    actions = ['copy_objects']


@admin.register(ValveOperationVariety)
class ValveOperationVarietyAdmin(AdminStructuredDataMixinCopyMixin, admin.ModelAdmin):
    list_display = ('name', 'code', 'sorting_order', 'is_active')
    list_editable = ('sorting_order', 'is_active')
    search_fields = ('name', 'code')
    actions = ['copy_objects']


@admin.register(ValveFunction)
class ValveFunctionAdmin(AdminStructuredDataMixinCopyMixin, admin.ModelAdmin):
    list_display = ('name', 'ports_count', 'positions_count', 'code', 'sorting_order', 'is_active')
    list_editable = ('sorting_order', 'is_active')
    list_filter = ('ports_count', 'positions_count', 'is_active')
    search_fields = ('name', 'code')
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description')
        }),
        ('Технические параметры', {
            'fields': ('ports_count', 'positions_count'),
            'description': 'Параметры линейности и позиционности'
        }),
        ('Настройки отображения', {
            'fields': ('sorting_order', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    actions = ['copy_objects']


@admin.register(ValveActuationVariety)
class ValveActuationVarietyAdmin(AdminStructuredDataMixinCopyMixin, admin.ModelAdmin):
    list_display = ('name', 'return_category', 'solenoids_count', 'code', 'sorting_order', 'is_active')
    list_editable = ('sorting_order', 'is_active')
    list_filter = ('return_category', 'solenoids_count', 'is_active')
    search_fields = ('name', 'code')
    actions = ['copy_objects']


@admin.register(ManualOverride)
class ManualOverrideAdmin(AdminStructuredDataMixinCopyMixin, admin.ModelAdmin):
    list_display = ('name', 'mechanism', 'has_fixation', 'code', 'sorting_order', 'is_active')
    list_editable = ('sorting_order', 'is_active', 'has_fixation')
    list_filter = ('mechanism', 'has_fixation', 'is_active')
    search_fields = ('name', 'code')
    actions = ['copy_objects']


@admin.register(ValvePilotVariety)
class ValvePilotVarietyAdmin(AdminStructuredDataMixinCopyMixin, admin.ModelAdmin):
    list_display = ('name', 'category', 'code', 'sorting_order', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'code')
    actions = ['copy_objects']
