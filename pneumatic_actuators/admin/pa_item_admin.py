# pneumatic_actuators/admin/pa_item_admin.py
"""Админка каталожных пневмоприводов — эталонная модель PneumaticActuatorCatalogItem.

Code генерируется автоматически в save() из model_line.model_item_code_template,
если не задан вручную; name/description — из шаблонов серии (TemplateMixin);
SKU — через SKUMixin.sync_sku() (только чтение в форме).
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.models.mixins import AdminCopyMixin
from pneumatic_actuators.models.pa_item import PneumaticActuatorCatalogItem


@admin.register(PneumaticActuatorCatalogItem)
class PneumaticActuatorCatalogItemAdmin(AdminCopyMixin, admin.ModelAdmin):
    """Админка каталожного пневмопривода."""

    list_display = (
        'code',
        'name',
        'model_line',
        'pneumatic_actuator_variety',
        'body',
        'sku',
        'sorting_order',
        'is_active',
        'origin',
    )
    list_editable = ('sorting_order', 'is_active')
    list_filter = (
        'is_active',
        'origin',
        'model_line',
        'pneumatic_actuator_variety',
    )
    search_fields = (
        'name',
        'code',
        'description',
        'model_line__name',
        'sku__code',
    )
    ordering = ('sorting_order', 'code')

    actions = ['copy_selected_objects']

    readonly_fields = ('sku',)  # SKU управляется sync_sku()

    def save_model(self, request, obj, form, change):
        if not change:
            # Карточка, созданная вручную в админке, — ручная: генератор её не трогает.
            obj.origin = PneumaticActuatorCatalogItem.Origin.MANUAL
        super().save_model(request, obj, form, change)

    filter_horizontal = ('tech_docs',)

    fieldsets = (
        (_('Основная информация'), {
            'fields': (
                'model_line',
                'body',
                'pneumatic_actuator_variety',
                ('code', 'name', 'description'),
            ),
        }),
        (_('Выбранные опции'), {
            'fields': (
                'selected_safety_position',
                'selected_springs_qty',
                'selected_temperature',
                'selected_ip',
                'selected_exd',
                'selected_body_coating',
                'selected_manual_override',
            ),
        }),
        (_('Номенклатура и медиа'), {
            'fields': ('equipment_type', 'sku', 'image_gallery', 'tech_docs'),
        }),
        (_('Настройки'), {
            'fields': ('sorting_order', 'is_active', 'extra_params'),
        }),
    )
