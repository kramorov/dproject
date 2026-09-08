# cable_glands/admin/metal_sleeve_admin.py
from django.contrib import admin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from cable_glands.models import MetalSleeve


@admin.register(MetalSleeve)
class MetalSleeveAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'sorting_order', 'description']
    list_editable = ['sorting_order', 'name', 'code']
    ordering = ['sorting_order', 'name']
    search_fields = ['name', 'code']

    actions = ['copy_selected']

    @admin.action(description=_("Скопировать выбранные металлорукава"))
    def copy_selected(self, request, queryset):
        """Копирование выбранных металлорукавов через MetalSleeve.create_copy()."""
        for original in queryset:
            original.create_copy()
        count = queryset.count()
        messages.success(request, _('Успешно скопировано %(count)d моделей') % {'count': count})
