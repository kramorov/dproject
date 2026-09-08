# cable_glands/admin/cg_model_line_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.admin_template_placeholders import TemplatePlaceholdersAdminMixin
from core.models.mixins import AdminCopyMixin

from cable_glands.models import CableGland, CableGlandModelLine


@admin.register(CableGlandModelLine)
class CableGlandModelLineAdmin(AdminCopyMixin, TemplatePlaceholdersAdminMixin, admin.ModelAdmin):
    """Админка серии кабельных вводов.

    Шаблоны name_template/description_template/model_item_code_template живут
    здесь; справочник плейсхолдеров строится по _get_data_dict() артикула
    (template_item_model=CableGland).
    """

    template_item_model = CableGland
    template_placeholders_fieldset = _('Шаблоны названия, описания и артикула')

    actions = ['copy_selected_objects']

    list_display = (
        'id', 'name', 'code', 'brand',
        'ip', 'exd_display',
        'for_armored_cable', 'for_metal_sleeve_cable', 'for_pipelines_cable',
        'temp_min', 'temp_max', 'sorting_order', 'is_active',
    )
    list_editable = ('sorting_order', 'is_active')
    list_filter = ('is_active', 'brand')
    search_fields = ('name', 'code', 'brand__name')
    ordering = ('sorting_order', 'name')

    filter_horizontal = ('exd', 'tech_docs', 'cert_docs')

    fieldsets = (
        (_('Общая информация'), {
            'fields': (
                ('name', 'code', 'brand', 'producer'),
                ('equipment_type', 'ip'),
                ('for_armored_cable', 'for_metal_sleeve_cable', 'for_pipelines_cable'),
                ('thread_external', 'thread_internal'),
                ('temp_min', 'temp_max'),
            ),
        }),
        (_('Шаблоны названия, описания и артикула'), {
            'fields': (
                ('name_template', 'description_template'),
                'model_item_code_template',
            ),
            'description': _('Шаблоны серии: {model_code}, {brand}, {thread}, '
                             '{body_material} — по справочнику плейсхолдеров ниже.'),
        }),
        (_('ГОСТ, Описание'), {
            'fields': ('gost', 'description'),
        }),
        (_('Медиа и документы'), {
            'fields': ('image_gallery', 'tech_docs', 'cert_docs'),
        }),
        (_('Настройки'), {
            'fields': ('sorting_order', 'is_active', 'extra_params'),
        }),
    )

    def exd_display(self, obj):
        """Отображение взрывозащиты в списке (разделитель ' / ')."""
        try:
            items = list(obj.exd.all())
        except Exception:
            items = []
        if not items:
            return '-'
        return ' / '.join(str(x) for x in items)

    exd_display.short_description = _('Взрывозащита')

    def get_queryset(self, request):
        """Оптимизация запросов списка серий."""
        return super().get_queryset(request).select_related(
            'brand', 'producer', 'ip', 'equipment_type',
        ).prefetch_related('exd')
