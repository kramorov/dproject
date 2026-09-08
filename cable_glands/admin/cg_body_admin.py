# cable_glands/admin/cg_body_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from cable_glands.models import (
    CableGlandBody,
    CableGlandMetalSleeveBody,
    CableGlandThreadOption,
)
from core.models.mixins import AdminCopyMixin


class CableGlandThreadOptionInline(admin.TabularInline):
    """Inline опций резьбы корпуса (через-таблица CableGlandBody ↔ ThreadSize)."""
    model = CableGlandThreadOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['thread_size', 'encoding', 'is_default', 'is_active', 'sorting_order']
    verbose_name = _("Опция резьбы")
    verbose_name_plural = _("Опции резьбы")


@admin.register(CableGlandBody)
class CableGlandBodyAdmin(AdminCopyMixin, admin.ModelAdmin):
    """Корпус кабельного ввода: диапазон обжимаемого кабеля + опции резьбы."""

    actions = ['copy_selected_objects']

    list_display = ('id', 'name', 'code', 'brand', 'cable_diameter_inner_min',
                    'cable_diameter_inner_max', 'thread_lenght', 'sorting_order', 'is_active')
    list_editable = ('sorting_order', 'is_active')
    list_filter = ('is_active', 'brand')
    search_fields = ('name', 'code')
    ordering = ('sorting_order', 'name')

    inlines = [CableGlandThreadOptionInline]

    fieldsets = (
        (_('Общая информация'), {
            'fields': (('name', 'code', 'brand'), 'description'),
        }),
        (_('Диаметр кабеля'), {
            'fields': (('cable_diameter_inner_min', 'cable_diameter_inner_max'),),
        }),
        (_('Размеры'), {
            'fields': ('thread_lenght',),
        }),
        (_('Настройки'), {
            'fields': ('sorting_order', 'is_active'),
        }),
    )

    def get_queryset(self, request):
        """Оптимизация запросов списка корпусов."""
        return super().get_queryset(request).select_related('brand').prefetch_related('cg_thread_body')


@admin.register(CableGlandMetalSleeveBody)
class CableGlandMetalSleeveBodyAdmin(AdminCopyMixin, admin.ModelAdmin):
    """Устройство для подключения металлорукава."""

    actions = ['copy_selected_objects']


    list_display = ('id', 'name', 'code', 'brand', 'metal_sleeve_display',
                    'metal_sleeve_inner', 'metal_sleeve_outer', 'sorting_order', 'is_active')
    list_editable = ('sorting_order', 'is_active')
    list_filter = ('is_active', 'brand')
    search_fields = ('name', 'code')
    ordering = ('sorting_order', 'name')

    filter_horizontal = ('metal_sleeve',)

    fieldsets = (
        (_('Общая информация'), {
            'fields': (('name', 'code', 'brand'), 'description'),
        }),
        (_('Металлорукав'), {
            'fields': ('metal_sleeve', ('metal_sleeve_inner', 'metal_sleeve_outer')),
        }),
        (_('Настройки'), {
            'fields': ('sorting_order', 'is_active'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('brand').prefetch_related('metal_sleeve')
