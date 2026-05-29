#gearbox/models/gb_model_line_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.models.mixins import AdminCopyMixin
from gearbox.models.gb_model_line import GearBoxModelLine


@admin.register(GearBoxModelLine)
class GearBoxModelLineAdmin(AdminCopyMixin, admin.ModelAdmin):
    filter_horizontal = ('tech_docs','cert_docs')
    list_display = ('name', 'code', 'brand',  'sorting_order', 'is_active')
    list_filter = ('is_active', 'brand', 'gearbox_output_variety')
    list_editable = ('sorting_order', 'is_active')
    search_fields = ('name', 'code', 'brand__name')
    ordering = ('sorting_order', 'name')
    actions = ['copy_selected_objects']

    fieldsets = (
        (None, {
            'fields': (('name', 'code'), ('brand', 'gearbox_output_variety', 'gearbox_variety','equipment_type'),('is_active', 'sorting_order'),)
        }),
        (_('Изображения и технички'), {
            'fields': ('image_gallery','tech_docs','cert_docs'),
        }),
        (_('Параметры') , {
            'fields' : (('name_template' ,'description_template','description',),('turn_angle','turn_tuning_limit', )) ,
        }) ,
        (_('Дополнительные параметры'), {
            'fields': ('extra_params',),
        }),
    )