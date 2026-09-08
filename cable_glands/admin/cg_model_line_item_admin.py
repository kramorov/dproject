# cable_glands/admin/cg_model_line_item_admin.py
"""Админка «модели в серии» (CableGlandModelLineItem).

Структурная связка: корпус (body) + устройство для подключения металлорукава
(metal_sleeve_body) + вес. Сам артикул каталога — CableGland (cg_actual_admin).
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.models.mixins import AdminCopyMixin

from cable_glands.models import CableGlandModelLineItem


@admin.register(CableGlandModelLineItem)
class CableGlandModelLineItemAdmin(AdminCopyMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'model_line', 'body', 'metal_sleeve_body',
                    'weight', 'sorting_order', 'is_active')
    list_editable = ('sorting_order', 'is_active')
    list_filter = ('is_active', 'model_line')
    search_fields = ('name', 'code', 'model_line__name')
    ordering = ('sorting_order', 'name')

    actions = ['copy_selected_objects']

    fieldsets = (
        (_('Общая информация'), {
            'fields': (
                'model_line',
                ('body', 'metal_sleeve_body'),
                'weight',
                ('name', 'code'),
                'description',
            ),
        }),
        (_('Настройки'), {
            'fields': ('sorting_order', 'is_active'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'model_line', 'body', 'metal_sleeve_body',
        )
