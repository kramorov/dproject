#filter_requlator/admin/fr_options_admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from filter_regulator.models import DrainVariety , FilterRegulatorVariety


@admin.register(DrainVariety)
class DrainVarietyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'sorting_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    ordering = ('sorting_order', 'name')


@admin.register(FilterRegulatorVariety)
class FilterRegulatorVarietyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'sorting_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    ordering = ('sorting_order', 'name')
