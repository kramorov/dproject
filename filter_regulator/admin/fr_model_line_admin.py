#filter_requlator/admin/fr_model_line_admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from filter_regulator.models import FilterRegulatorModelLine


@admin.register(FilterRegulatorModelLine)
class FilterRegulatorModelLineAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'brand', 'is_active', 'sorting_order')
    list_filter = ('is_active', 'brand', 'body_material', 'bowl_material')
    search_fields = ('name', 'code', 'brand__name')
    ordering = ('brand', 'sorting_order', 'name')

    fieldsets = (
        (None, {
            'fields': ('name', ('code', 'brand','filter_variety'), 'description', ('is_active', 'sorting_order'),)
        }),
        (_('Шаблоны'), {
            'fields': ('name_template', 'description_template'),
            'classes': ('wide',),
        }),
        (_('Материалы'), {
            'fields': (('body_material', 'body_material_specified','body_material_text',), ('bowl_material', 'bowl_material_text'),'protection_material')
        }),
        (_('Рабочие параметры'), {
            'fields': (('work_temp_min', 'work_temp_max'), ('pressure_min', 'pressure_max', 'pressure_inlet_max'))
        }),
        (_('Дополнительные параметры'), {
            'fields': ('extra_params',),
            'classes': ('wide',),
        }),
    )