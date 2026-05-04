#filter_requlator/admin/fr_body_admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from filter_regulator.models import FilterRegulatorBody


@admin.register(FilterRegulatorBody)
class FilterRegulatorBodyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'weight', 'thread', 'gauge_port_size', 'drain_port_size', 'is_active', 'sorting_order')
    list_filter = ('is_active', 'thread', 'gauge_port_size', 'drain_port_size')
    search_fields = ('name', 'code')
    ordering = ('sorting_order', 'name')
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description', 'weight', 'is_active', 'sorting_order')
        }),
        (_('Резьбы'), {
            'fields': ('thread', 'gauge_port_size', 'drain_port_size')
        }),
        (_('Дополнительные параметры'), {
            'fields': ('extra_params',),
            'classes': ('wide',),
            'description': _('JSON формат: {"material": "aluminum", "features": ["filter", "regulator"]}')
        }),
    )