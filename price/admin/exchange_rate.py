# price/admin/exchange_rate.py
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path
from django.shortcuts import render, redirect
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from django.db import models
from rangefilter.filters import DateRangeFilter  # pip install django-admin-rangefilter
from import_export.admin import ImportExportModelAdmin, ImportExportActionModelAdmin  # pip install django-import-export
from import_export import resources
from datetime import date, datetime

from price.models.exchange_rate import ExchangeRate
from price.services.cbr_exchange import CBRExchangeService

import logging


logger = logging.getLogger(__name__)

class ExchangeRateResource(resources.ModelResource):
    class Meta:
        model = ExchangeRate
        import_id_fields = ('currency', 'date')
        skip_unchanged = True
        report_skipped = True


@admin.register(ExchangeRate)
class ExchangeRateAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    """Админка для курсов валют"""

    resource_class = ExchangeRateResource

    # ======== СПИСОК ========
    list_display = (
        'currency_colored',
        'date',
        'rate_display',
        'nominal',
        'rate_per_one_display',
    )
    list_filter = (
        'currency',
        ('date', DateRangeFilter),
        'created_at',
    )
    search_fields = ('currency',)
    date_hierarchy = 'date'
    ordering = ('-date', 'currency')
    list_per_page = 20

    # ======== РЕДАКТИРОВАНИЕ ========
    fieldsets = (
        (None, {
            'fields': (
                ('currency', 'date'),
                ('rate', 'nominal'),
            )
        }),
        (_('Служебная информация'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'rate_per_one')

    class Media:
        js = ('price/js/add_rates_button.js',)

    # ======== ДЕЙСТВИЯ ========
    actions = ['update_from_cbr', 'copy_selected']

    @admin.display(description=_('Курс'), ordering='rate')
    def rate_display(self, obj):
        # Просто строка, без format_html
        return f"{float(obj.rate):.2f} ₽"

    @admin.display(description=_('Курс за 1 ед.'))
    def rate_per_one_display(self, obj):
        return f"{float(obj.rate_per_one):.4f} ₽"

    @admin.display(description=_('Валюта'), ordering='currency')
    def currency_colored(self, obj):
        colors = {
            'USD': 'green',
            'EUR': 'blue',
            'CNY': 'red',
        }
        color = colors.get(obj.currency, 'gray')
        # Безопасный HTML через mark_safe
        from django.utils.safestring import mark_safe
        return mark_safe(f'<span style="color: {color}; font-weight: bold;">{obj.currency}</span>')

    @admin.action(description=_("Обновить курсы с сайта ЦБ РФ"))
    def update_from_cbr(self, request, queryset):
        """Обновить выбранные курсы из ЦБ"""
        updated = 0
        errors = 0

        for rate in queryset:
            try:
                CBRExchangeService.fetch_and_save_rates(rate.date)
                updated += 1
            except Exception as e:
                errors += 1
                logger.error(f"Ошибка обновления {rate.currency} на {rate.date}: {e}")

        message = f"Обновлено: {updated}, ошибок: {errors}"
        self.message_user(request, message)

    @admin.action(description=_("Копировать выбранные"))
    def copy_selected(self, request, queryset):
        """Копировать записи с изменением даты"""
        if 'apply' in request.POST:
            new_date = request.POST.get('new_date')
            if new_date:
                count = 0
                for rate in queryset:
                    rate.pk = None
                    rate.date = new_date
                    rate.save()
                    count += 1
                self.message_user(request, f"Создано копий: {count}")
                return

        context = {
            'title': _("Копировать курсы"),
            'object_name': 'ExchangeRate',
            'queryset': queryset,
            'action': 'copy_selected',
            'opts': self.model._meta,
        }
        return render(request, 'admin/exchange_rate_copy_intermediate.html', context)

    # ======== КАСТОМНЫЕ URL ========
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('add-rates/',
                 self.admin_site.admin_view(self.add_rates_view),
                 name='price_exchangerate_add_rates'),
        ]
        return custom_urls + urls

    # ======== КАСТОМНОЕ ПРЕДСТАВЛЕНИЕ ========
    def add_rates_view(self, request):
        """Страница добавления курсов валют на дату"""
        context = {
            'title': _("Добавить курсы валют на дату"),
            'opts': self.model._meta,
            'media': self.media,
            'currencies': ['USD', 'EUR', 'CNY'],
            'today': date.today(),
            'has_change_permission': self.has_change_permission(request),
            'is_popup': False,
            'save_as': False,
            'add': False,
            'change': True,
            'show_delete': False,
            'has_add_permission': self.has_add_permission(request),
            'has_view_permission': self.has_view_permission(request),
            'has_editable_inline_admin_formsets': False,
        }

        if request.method == 'POST':
            target_date = request.POST.get('target_date')
            currencies = request.POST.getlist('currencies')

            if not target_date:
                self.message_user(request, _("Выберите дату"), level='ERROR')
                return redirect('admin:price_exchangerate_changelist')

            try:
                target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
                rates = CBRExchangeService.fetch_and_save_rates(target_date)

                if currencies:
                    for currency in list(rates.keys()):
                        if currency not in currencies:
                            del rates[currency]

                self.message_user(
                    request,
                    _("Добавлено курсов на {date}: {count}").format(
                        date=target_date.strftime('%d.%m.%Y'),
                        count=len(rates)
                    )
                )
            except Exception as e:
                self.message_user(
                    request,
                    _("Ошибка: {error}").format(error=str(e)),
                    level='ERROR'
                )

            return redirect('admin:price_exchangerate_changelist')

        return render(request, 'admin/exchangerate_add_rates.html', context)

    # ======== КАСТОМНЫЙ СПИСОК ========
    def changelist_view(self, request, extra_context=None):
        """Добавляем сегодняшние курсы и кнопку обновления в шапку списка"""
        from django.urls import reverse
        from datetime import date

        extra_context = extra_context or {}

        # Получаем курсы на сегодня
        extra_context['today_rates'] = ExchangeRate.objects.filter(
            date=date.today()
        ).order_by('currency')
        extra_context['today'] = date.today()

        # Добавляем URL для быстрого обновления
        extra_context['cbr_update_url'] = reverse('price:cbr-update')

        # ИЗМЕНИТЬ ЭТУ СТРОКУ:
        extra_context['add_rates_url'] = 'add-rates/'  # относительный URL, без reverse

        # Добавляем информацию о последнем обновлении
        last_update = ExchangeRate.objects.filter(
            date=date.today()
        ).aggregate(
            last=models.Max('updated_at')
        )['last']
        extra_context['last_update'] = last_update

        return super().changelist_view(request, extra_context)



