# cable_glands/admin/metal_sleeve_admin.py
from django.contrib import admin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from typing import List, Optional, Tuple, Any, Dict, Union

# import logging
#
# # Получаем логгер
# logger = logging.getLogger(__name__)

class MetalSleeveAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'sorting_order','description']
    list_editable = ['sorting_order', 'name', 'code']
    ordering = ['sorting_order', 'name']
    search_fields = ['name']
    # Добавьте в list_display кнопку действий
    actions = ['copy_selected']

    class Meta:
        verbose_name = _("Тип металлорукава")
        verbose_name_plural = _("Типы металлорукава")
        ordering = ['sorting_order']

    def copy_selected(self, request, queryset):
        """Копирование выбранных моделей"""
        for original in queryset:
            original.create_copy()

        count = queryset.count()
        messages.success(request, f'Успешно скопировано {count} моделей')