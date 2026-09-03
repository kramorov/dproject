# pa_controls/admin/posi_constructor_admin.py
"""
Админка конструктора позиционеров (PositionerConstructor).

Паттерн — pneumatic_actuators/admin/pa_constructor_admin.py:
list_display со всеми опциями, select_related в get_queryset,
readonly name/code/is_unique (генерируются в save()).
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from pa_controls.models import PositionerConstructor


@admin.register(PositionerConstructor)
class PositionerConstructorAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code',
        'selected_model_line', 'selected_body_connection', 'selected_lever',
        'selected_temperature', 'selected_signal_profile', 'selected_alarm',
        'selected_exd_row', 'selected_exd',
        'is_unique', 'is_active', 'description_preview',
    ]
    list_filter = ['is_active', 'is_unique', 'selected_model_line']
    search_fields = ['name', 'code', 'description']
    autocomplete_fields = ['selected_model_line']
    readonly_fields = ['name', 'code', 'is_unique']
    list_select_related = [
        'selected_model_line',
        'selected_body_connection',
        'selected_lever',
        'selected_temperature',
        'selected_signal_profile',
        'selected_alarm',
        'selected_exd_row',
        'selected_exd',
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(*self.list_select_related)

    fieldsets = (
        (None, {
            'fields': (
                ('selected_model_line',),
                ('selected_body_connection', 'selected_lever'),
                ('selected_temperature',),
                ('selected_signal_profile_option', 'selected_signal_profile'),
                ('selected_smart_capability_set',),
                ('selected_alarm',),
                ('selected_exd_row', 'selected_exd'),
                ('work_temp_min', 'work_temp_max'),
                ('name', 'code', 'description'),
                ('is_unique', 'is_active', 'sorting_order'),
            ),
        }),
    )

    def description_preview(self, obj):
        return (obj.description or '')[:120]

    description_preview.short_description = _('Описание (превью)')
