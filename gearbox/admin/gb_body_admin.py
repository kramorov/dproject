#gearbox/admin/gb_body_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from gearbox.models import GearBoxBody


@admin.register(GearBoxBody)
class GearBoxBodyAdmin(admin.ModelAdmin):
    """Админка для корпусов редукторов"""

    list_display = (
    'name', 'code', 'transmission_variety', 'reduction_ratio', 'efficiency', 'sorting_order', 'is_active')
    list_filter = ('is_active', 'transmission_variety')
    list_editable = ('sorting_order', 'is_active')
    search_fields = ('name', 'code', 'description')
    ordering = ('sorting_order', 'name')

    fieldsets = (
        (None, {
            'fields': (('name', 'code', 'transmission_variety'),)
        }),

        (_('Передаточные характеристики'), {
            'fields': (('reduction_ratio', 'reduction_ratio_text', 'reduction_ratio_verified'),
                       ('amplification_factor', 'amplification_factor_verified'), ('efficiency','mechanical_advantage','weight'),)
        }),
        (_('Моменты и усилие'), {
            'fields': (('max_input_torque', 'max_output_torque'), ('handwheel_force_nominal', 'handwheel_diameter'))
        }),
        (_('Присоединение сверху (к приводу)'), {
            'fields': ('mounting_plate_top', ('stem_shape_top', 'stem_size_top', 'stem_height_top'))
        }),
        (_('Присоединение снизу (к арматуре)'), {
            'fields': ('mounting_plate_bottom', ('stem_shape_bottom', 'stem_size_bottom',
                       'stem_height_bottom', 'max_stem_diameter_bottom'))
        }),
        (_('Дополнительные параметры'), {
            'fields': (('is_active', 'sorting_order'),)
        }),
        (_('Описание') , {
            'fields' : ('description',)
        }) ,
    )

    filter_horizontal = ('mounting_plate_top', 'mounting_plate_bottom')