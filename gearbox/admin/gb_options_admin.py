#gearbox/admin/gb_options_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from gearbox.models import OverrideMechanism, TransmissionVariety


@admin.register(OverrideMechanism)
class OverrideMechanismAdmin(admin.ModelAdmin):
    """Админка для механизмов отключения/дублирования"""

    list_display = ('name', 'code', 'sorting_order', 'is_active')
    list_filter = ('is_active',)
    list_editable = ('sorting_order', 'is_active')
    search_fields = ('name', 'code', 'description')
    ordering = ('sorting_order', 'name')

    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description', 'is_active', 'sorting_order')
        }),

    )

    @admin.register(TransmissionVariety)
    class TransmissionVarietyAdmin(admin.ModelAdmin):
        """Админка для механизмов передачи (червячная, коническая, планетарная и т.д.)"""

        list_display = ('name', 'code', 'sorting_order', 'is_active')
        list_filter = ('is_active',)
        list_editable = ('sorting_order', 'is_active')
        search_fields = ('name', 'code', 'description')
        ordering = ('sorting_order', 'name')

        fieldsets = (
            (None, {
                'fields': ('name', 'code', 'description', 'is_active', 'sorting_order')
            }),
        )