# electric_actuators/admin/ea_access_device_admin.py
"""Админка устройства ограничения несанкционированного доступа ЭП.

- ``EaAccessDeviceOption`` — справочник вариантов (NO_DEVICE / DEVICE);
- ``ControlUnitAccessDeviceOption`` — через-модель БУ×вариант: редактируется
  инлайном в админке ``params.ControlUnitInstalledOption`` (источник —
  «для блока управления доступны варианты»).
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from electric_actuators.models import EaAccessDeviceOption


@admin.register(EaAccessDeviceOption)
class EaAccessDeviceOptionAdmin(admin.ModelAdmin):
    """Справочник вариантов устройства ограничения доступа (локализованный)."""

    list_display = ('code', 'name', 'sorting_order', 'is_active')
    list_editable = ('sorting_order', 'is_active')
    search_fields = ('code', 'name')
    ordering = ('sorting_order', 'code')

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('code', 'name', 'description')
        }),
        (_('Локализация'), {
            'fields': ('name_i18n', 'description_i18n'),
            'classes': ('collapse',),
        }),
        (_('Настройки'), {
            'fields': ('sorting_order', 'is_active')
        }),
    )
