# cable_glands/admin/cg_actual_admin.py
"""Админка артикула каталога CableGland.

Артикул — конкретный кабельный ввод: серия (CableGlandModelLine) +
«модель в серии» (CableGlandModelLineItem: корпус/металлорукав/вес) +
выбранные резьба (thread) и материал корпуса (body_material).

name/description генерируются из шаблонов серии (TemplateMixin.save());
code вводится вручную (автогенерация из model_item_code_template — с реестром полей);
SKU создаётся автоматически (SKUMixin.sync_sku()), в форме — только чтение.
"""

from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.models.mixins import AdminCopyMixin

from cable_glands.models import CableGland, CableGlandModelLine


class CableGlandAdminForm(forms.ModelForm):
    class Meta:
        model = CableGland
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        # Серия (источник шаблонов) автозаполняется из «модели в серии»,
        # если не выбрана явно (дублирует логику CableGland.save()).
        model_line = cleaned_data.get('model_line')
        model_line_item = cleaned_data.get('model_line_item')
        if not model_line and model_line_item and model_line_item.model_line_id:
            cleaned_data['model_line'] = model_line_item.model_line
        # code не требуется: при пустом коде save() автогенерирует артикул
        # из model_line.model_item_code_template (см. CableGland.save()).
        return cleaned_data


@admin.register(CableGland)
class CableGlandAdmin(AdminCopyMixin, admin.ModelAdmin):
    """Админка артикула кабельного ввода."""

    form = CableGlandAdminForm

    list_display = (
        'code', 'name', 'model_line', 'model_line_item',
        'thread', 'body_material', 'sku', 'sorting_order', 'is_active',
    )
    list_editable = ('sorting_order', 'is_active')
    list_filter = ('is_active', 'model_line', 'body_material')
    search_fields = ('code', 'name', 'description', 'model_line__name', 'sku__code')
    ordering = ('sorting_order', 'code')

    actions = ['copy_selected_objects']

    readonly_fields = ('sku',)  # SKU управляется sync_sku()

    filter_horizontal = ('tech_docs',)

    fieldsets = (
        (_('Основная информация'), {
            'fields': (
                'model_line',
                'model_line_item',
                'thread',
                'body_material',
                ('code', 'name', 'description'),
            ),
        }),
        (_('Номенклатура и медиа'), {
            'fields': ('sku', 'image_gallery', 'tech_docs'),
        }),
        (_('Настройки'), {
            'fields': ('sorting_order', 'is_active'),
        }),
    )

    def get_queryset(self, request):
        """Оптимизация запросов списка артикулов."""
        return super().get_queryset(request).select_related(
            'model_line', 'model_line_item', 'model_line_item__body',
            'model_line_item__metal_sleeve_body', 'thread', 'body_material', 'sku',
        )
