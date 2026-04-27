#pa_controls/admin/pa_control_mounting_admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from pa_controls.models import PaControlMountingStandard


@admin.register(PaControlMountingStandard)
class PaControlMountingStandardAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'standard_type', 'size', 'square_size_mm',
        'mounting_holes_x_mm', 'mounting_holes_y_mm', 'screw_thread',
        'sorting_order', 'is_active'
    ]
    list_filter = ['is_active', 'standard_type', 'size', 'screw_thread']
    search_fields = ['name', 'code', 'description', 'size']
    list_editable = ['sorting_order', 'is_active']
    ordering = ['sorting_order', 'name']

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'code', 'description', 'standard_type', 'size')
        }),
        (_('Геометрия'), {
            'fields': ('square_size_mm', 'screw_thread', 'mounting_holes_x_mm', 'mounting_holes_y_mm')
        }),
        (_('Дополнительные отверстия'), {
            'fields': ('has_additional_holes', 'additional_holes_pattern')
        }),
        (_('Совместимость'), {
            'fields': ('compatible_sizes',)
        }),
        (_('Дополнительные параметры'), {
            'fields': ('extra_params',),
            'classes': ('wide',),
        }),
        (_('Настройки'), {
            'fields': ('sorting_order', 'is_active')
        }),
    )

    def get_display_name(self, obj):
        return obj.get_display_name()

    get_display_name.short_description = _('Отображаемое имя')