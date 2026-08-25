# pa_controls/admin/positioner_admin.py
"""Админка позиционеров: справочники, серии с through-опциями, модели."""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from pa_controls.models import (
    ActingType,
    LeverOption,
    SmartCapabilityOption,
    SmartCapabilitySet,
    PosiModelLine,
    PosiModelLineItem,
)
from pa_controls.models.posi_model_line import (
    PosiActingTypeOption,
    PosiCableGlandHolesOption,
    PosiPneumaticThreadOption,
    PosiPneumaticConnectionOption,
    PosiLeverOption,
    PosiTemperatureOption,
    PosiSignalProfileOption,
    PosiAlarmOption,
)


# ── Справочники ──

@admin.register(ActingType)
class ActingTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'sorting_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    list_editable = ['code', 'sorting_order', 'is_active']
    ordering = ['sorting_order', 'code']


@admin.register(LeverOption)
class LeverOptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'length_mm', 'sorting_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    list_editable = ['code', 'length_mm', 'sorting_order', 'is_active']
    ordering = ['length_mm', 'sorting_order', 'code']


@admin.register(SmartCapabilityOption)
class SmartCapabilityOptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'sorting_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    list_editable = ['code', 'sorting_order', 'is_active']
    ordering = ['sorting_order', 'code']


@admin.register(SmartCapabilitySet)
class SmartCapabilitySetAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'sorting_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    list_editable = ['code', 'sorting_order', 'is_active']
    filter_horizontal = ['capabilities']
    ordering = ['sorting_order', 'code']


# ── Inline-опции серии ──

class PosiActingTypeOptionInline(admin.TabularInline):
    model = PosiActingTypeOption
    extra = 0
    fields = ['acting_type', 'encoding', 'is_default', 'sorting_order', 'is_active']


class PosiCableGlandHolesOptionInline(admin.TabularInline):
    model = PosiCableGlandHolesOption
    extra = 0
    fields = ['cg_set', 'encoding', 'is_default', 'sorting_order', 'is_active']


class PosiPneumaticThreadOptionInline(admin.TabularInline):
    model = PosiPneumaticThreadOption
    extra = 0
    fields = ['thread_size', 'encoding', 'is_default', 'sorting_order', 'is_active']


class PosiPneumaticConnectionOptionInline(admin.TabularInline):
    model = PosiPneumaticConnectionOption
    extra = 0
    fields = ['pneumatic_connection', 'encoding', 'is_default', 'sorting_order', 'is_active']


class PosiLeverOptionInline(admin.TabularInline):
    model = PosiLeverOption
    extra = 0
    fields = ['lever', 'encoding', 'is_default', 'sorting_order', 'is_active']


class PosiTemperatureOptionInline(admin.TabularInline):
    model = PosiTemperatureOption
    extra = 0
    fields = ['work_temp_min', 'work_temp_max', 'encoding', 'is_default', 'sorting_order', 'is_active']


class PosiSignalProfileOptionInline(admin.TabularInline):
    model = PosiSignalProfileOption
    extra = 0
    fields = ['signal_profile', 'encoding', 'is_default', 'sorting_order', 'is_active']


class PosiAlarmOptionInline(admin.TabularInline):
    model = PosiAlarmOption
    extra = 0
    fields = ['alarm', 'encoding', 'is_default', 'sorting_order', 'is_active']


# ── Серия ──

@admin.register(PosiModelLine)
class PosiModelLineAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'brand', 'actuator_action', 'body_material', 'is_active']
    list_filter = ['actuator_action', 'body_material', 'is_active']
    search_fields = ['name', 'code']
    list_editable = ['code', 'actuator_action', 'is_active']
    autocomplete_fields = ['smart_capability_set']
    raw_id_fields = ['brand', 'producer', 'body_material']
    filter_horizontal = ['exd']
    ordering = ['sorting_order', 'code']
    inlines = [
        PosiActingTypeOptionInline,
        PosiCableGlandHolesOptionInline,
        PosiPneumaticThreadOptionInline,
        PosiPneumaticConnectionOptionInline,
        PosiLeverOptionInline,
        PosiTemperatureOptionInline,
        PosiSignalProfileOptionInline,
        PosiAlarmOptionInline,
    ]
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'code', 'equipment_type', 'brand', 'producer', 'description'),
        }),
        (_('Характеристики'), {
            'fields': ('body_material', 'weight',
                       ('supply_pressure_min', 'supply_pressure_max'),
                       'actuator_action'),
        }),
        (_('Взрывозащита и смарт-возможности'), {
            'fields': ('exd', 'smart_capability_set'),
        }),
        (_('Шаблоны'), {
            'fields': ('name_template', 'description_template'),
        }),
        (_('Дополнительно'), {
            'fields': ('extra_params', 'sorting_order', 'is_active'),
        }),
    )


# ── Модель (item) ──

@admin.register(PosiModelLineItem)
class PosiModelLineItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'model_line', 'acting_type', 'exd', 'is_active']
    list_filter = ['model_line', 'acting_type', 'exd', 'is_active']
    search_fields = ['name', 'code']
    autocomplete_fields = [
        'model_line', 'acting_type', 'exd', 'ip', 'lever', 'smart_capability_set',
    ]
    raw_id_fields = [
        'cable_glands_holes', 'pneumatic_connection', 'pneumatic_connection_thread',
        'alarm', 'signal_profile',
    ]
    ordering = ['sorting_order', 'code']
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'code', 'model_line', 'description'),
        }),
        (_('Опции'), {
            'fields': ('acting_type', 'exd', 'ip',
                       'cable_glands_holes',
                       'pneumatic_connection', 'pneumatic_connection_thread',
                       'lever', ('work_temp_min', 'work_temp_max')),
        }),
        (_('Сигналы'), {
            'fields': ('signal_profile', 'alarm'),
        }),
        (_('Смарт-возможности'), {
            'fields': ('smart_capability_set',),
        }),
        (_('Дополнительно'), {
            'fields': ('extra_params', 'sorting_order', 'is_active'),
        }),
    )
