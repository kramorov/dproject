#filter_requlator/admin/fr_model_line_admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.admin_template_placeholders import TemplatePlaceholdersAdminMixin
from core.admin_regenerate_items import RegenerateSeriesItemsAdminMixin
from filter_regulator.models import FilterRegulatorModelLine
from filter_regulator.models.fr_model_line_item import FilterRegulator


@admin.register(FilterRegulatorModelLine)
class FilterRegulatorModelLineAdmin(RegenerateSeriesItemsAdminMixin, TemplatePlaceholdersAdminMixin, admin.ModelAdmin):
    template_item_model = FilterRegulator
    regenerate_items_related_name = 'filter_model_line'
    list_display = ('name', 'code', 'brand', 'is_active', 'sorting_order')
    list_filter = ('is_active', 'brand', 'body_material', 'bowl_material')
    search_fields = ('name', 'code', 'brand__name')
    ordering = ('brand', 'sorting_order', 'name')
    filter_horizontal = ('tech_docs', 'cert_docs')
    fieldsets = (
        (None, {
            'fields': ('name', ('code', 'brand','filter_variety'),'equipment_type', 'description', 'description_i18n', ('is_active', 'sorting_order'),)
        }),
        (_('Шаблоны'), {
            'fields': ('name_template', 'name_template_i18n', 'description_template', 'description_template_i18n'),
            'classes': ('wide',),
        }),
        (_('Материалы'), {
            'fields': (
                ('body_material', 'body_material_specified', 'body_material_text'),
                'body_material_text_i18n',
                ('bowl_material', 'bowl_material_text'),
                'bowl_material_text_i18n',
                'protection_material',
                'protection_material_i18n',
            )
        }),
        (_('Рабочие параметры'), {
            'fields': (('work_temp_min', 'work_temp_max'), ('pressure_min', 'pressure_max', 'pressure_inlet_max'))
        }),
        (_('Изображения и технички'), {
            'fields': ('image_gallery', 'tech_docs', 'cert_docs'),
        }),
        (_('Дополнительные параметры'), {
            'fields': ('extra_params',),
            'classes': ('wide',),
        }),
    )