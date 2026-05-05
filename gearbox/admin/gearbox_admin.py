#gearbox/admin/gearbox_admin.py

from django.contrib import admin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from gearbox.models import GearBox


@admin.register(GearBox)
class GearBoxAdmin(admin.ModelAdmin):
    """Админка для редукторов"""

    list_display = ('name', 'code', 'model_line', 'body',  'sorting_order', 'is_active')
    list_filter = ('is_active', 'model_line', 'body', )
    list_editable = ('sorting_order', 'is_active')
    # search_fields = ('name', 'code', 'model_line__name', 'description')
    ordering = ('sorting_order', 'name')
    actions = ['copy_selected_objects']

    fieldsets = (
        (None, {
            'fields': ('name', 'code',  'model_line', 'is_active', 'sorting_order')
        }),
        (_('Корпус и механизмы'), {
            'fields': (('body', 'body_material_text'),('override_mechanism', 'locking_mechanism', 'is_declutchable'))
        }),
        (_('Температурные режимы'), {
            'fields': (('work_temp_min', 'work_temp_max'),('ip', 'interlock'))
        }),

        (_('Дополнительные параметры'), {
            'fields': ('extra_params','description',),
            'classes': ('wide',),
            'description': _('JSON формат: {"key": "value"}')
        }),
    )

    def copy_selected_objects(self, request, queryset):
        """Копирование выбранных редукторов"""
        copied_count = 0
        errors = []

        for obj in queryset:
            try:
                if hasattr(obj, 'copy'):
                    obj.copy()
                else:
                    obj.pk = None
                    obj.save()
                copied_count += 1
            except Exception as e:
                errors.append(f"{obj.name}: {str(e)}")

        if copied_count > 0:
            self.message_user(request, f"✅ Скопировано {copied_count} редукторов", level=messages.SUCCESS)
        if errors:
            self.message_user(request, f"⚠️ Ошибки: {', '.join(errors)}", level=messages.ERROR)

    copy_selected_objects.short_description = "📋 Копировать выбранные редукторы"