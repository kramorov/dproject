# valve_data/admin/admin_torque_characteristics.py
from django.contrib import admin
from django.forms import modelformset_factory
from django.shortcuts import redirect, render
from django.urls import path

from valve_data.models import (
    SealType,
    TorquePoint,
    ValveSupportType,
    ValveTorqueCoefficient,
)


@admin.register(SealType)
class SealTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'sorting_order', 'is_active')
    list_editable = ('sorting_order', 'is_active')
    search_fields = ('code', 'name')
    ordering = ('sorting_order', 'id')


@admin.register(ValveSupportType)
class ValveSupportTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'sorting_order', 'is_active')
    list_editable = ('sorting_order', 'is_active')
    search_fields = ('code', 'name')
    ordering = ('sorting_order', 'id')


@admin.register(TorquePoint)
class TorquePointAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'direction', 'position', 'sorting_order', 'is_active')
    list_editable = ('sorting_order', 'is_active')
    list_filter = ('direction', 'position', 'is_active')
    search_fields = ('code', 'name')
    ordering = ('sorting_order', 'id')


@admin.register(ValveTorqueCoefficient)
class ValveTorqueCoefficientAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'valve_type', 'support', 'seal_type',
                    'bto', 'rto', 'eto', 'btc', 'rtc', 'etc', 'is_active')
    list_editable = ('bto', 'rto', 'eto', 'btc', 'rtc', 'etc')
    list_filter = ('valve_type', 'support', 'seal_type', 'is_active')
    search_fields = ('code', 'name', 'valve_type__code', 'valve_type__name')
    ordering = ('valve_type__sorting_order', 'sorting_order', 'id')
    actions = ('mirror_close_from_open_action',)
    change_list_template = 'admin/valve_data/valvetorquecoefficient/change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('table/', self.admin_site.admin_view(self.table_view),
                 name='valve_data_valvetorquecoefficient_table'),
        ]
        return custom + urls

    @admin.action(description='Заполнить закрытие зеркалом открытия')
    def mirror_close_from_open_action(self, request, queryset):
        updated = 0
        for obj in queryset:
            if obj.mirror_close_from_open():
                obj.save(update_fields=['btc', 'rtc', 'etc'])
                updated += 1
        self.message_user(request, f'Закрытие заполнено зеркалом открытия: {updated} стр(ок) обновлено.')

    def table_view(self, request):
        """Все таблицы коэффициентов на одной странице (форма для редактирования)."""
        formset_cls = modelformset_factory(
            ValveTorqueCoefficient,
            fields=('bto', 'rto', 'eto', 'btc', 'rtc', 'etc'),
            extra=0,
        )
        qs = (ValveTorqueCoefficient.objects
              .select_related('valve_type', 'support', 'seal_type')
              .order_by('valve_type__sorting_order', 'sorting_order', 'id'))

        if request.method == 'POST':
            formset = formset_cls(request.POST, queryset=qs)
            if formset.is_valid():
                formset.save()
                self.message_user(request, 'Таблица коэффициентов сохранена.')
                return redirect(request.path)
        else:
            formset = formset_cls(queryset=qs)

        context = {
            **self.admin_site.each_context(request),
            'title': 'Таблица коэффициентов момента',
            'opts': self.model._meta,
            'formset': formset,
            'has_view_permission': self.has_view_permission(request),
            'has_change_permission': self.has_change_permission(request),
        }
        return render(request, 'admin/valve_data/valvetorquecoefficient/table.html', context)
