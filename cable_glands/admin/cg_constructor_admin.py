# cable_glands/admin/cg_constructor_admin.py
"""Админка конструктора кабельных вводов (CableGlandConstructor)."""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from cable_glands.models import CableGlandConstructor


@admin.register(CableGlandConstructor)
class CableGlandConstructorAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code',
        'selected_model_line', 'selected_model_line_item',
        'selected_thread_option', 'selected_body_material_option',
        'selected_exd_option',
        'is_unique', 'is_active', 'description_preview',
    ]
    list_filter = ['is_active', 'is_unique', 'selected_model_line']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['name', 'code', 'is_unique']

    list_select_related = [
        'selected_model_line',
        'selected_model_line_item',
        'selected_thread_option__thread_size',
        'selected_body_material_option__body_material',
        'selected_exd_option',
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(*self.list_select_related)

    fieldsets = (
        (None, {
            'fields': (
                ('selected_model_line', 'selected_model_line_item'),
                ('selected_thread_option', 'selected_body_material_option', 'selected_exd_option'),
                ('name', 'code', 'description'),
                ('is_unique', 'is_active', 'sorting_order'),
            ),
        }),
    )

    def description_preview(self, obj):
        return (obj.description or '')[:120]

    description_preview.short_description = _('Описание (превью)')
