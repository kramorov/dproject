#gearbox/admin/interlock_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from gearbox.models import GearBoxInterlock


@admin.register(GearBoxInterlock)
class GearBoxInterlockAdmin(admin.ModelAdmin):
    """Админка для интерлоков редуктора"""

    list_display = ('name', 'code', 'interlock_ip', 'interlock_points', 'sorting_order', 'is_active')
    list_filter = ('is_active', 'interlock_ip', 'interlock_sensor_variety')
    list_editable = ('sorting_order', 'is_active')
    search_fields = ('name', 'code', 'description')
    ordering = ('sorting_order', 'name')
    actions = ['copy_selected_objects']

    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description', 'is_active', 'sorting_order')
        }),
        (_('Защита интерлока'), {
            'fields': ('interlock_ip', 'interlock_exd')
        }),
        (_('Датчики интерлока'), {
            'fields': ('interlock_sensor_variety', 'interlock_sensor_components', 'interlock_points'),
        }),
    )

    filter_horizontal = ('interlock_exd', 'interlock_sensor_components')