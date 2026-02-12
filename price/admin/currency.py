# price/admin/currency.py
from django.contrib import admin
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db import models
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from rangefilter.filters import DateRangeFilter
from django.contrib.admin import SimpleListFilter

from price.models.currency import Currency, PriceVariety, PriceHistory


# class NameFilter(SimpleListFilter):
#     title = 'Название'
#     parameter_name = 'name'
#
#     def lookups(self, request, model_admin):
#         return [('search', 'Поиск...')]
#
#     def queryset(self, request, queryset):
#         value = self.value()
#         if value and value != 'search':
#             return queryset.filter(name__icontains=value)
#         return queryset
#
#
# class CodeFilter(SimpleListFilter):
#     title = 'Код'
#     parameter_name = 'code'
#
#     def lookups(self, request, model_admin):
#         return [('search', 'Поиск...')]
#
#     def queryset(self, request, queryset):
#         value = self.value()
#         if value and value != 'search':
#             return queryset.filter(code__icontains=value)
#         return queryset
#
#     def choices(self, changelist):
#         value = self.value() or ''
#         yield {
#             'selected': False,
#             'query_string': changelist.get_query_string({self.parameter_name: ''}, []),
#             'display': format_html(
#                 '<input type="text" name="{}" value="{}" placeholder="{}" style="width: 150px; padding: 5px;" '
#                 'onchange="window.location.href=this.form.action+\'?\'+this.name+\'=\'+encodeURIComponent(this.value)">',
#                 self.parameter_name, value, _('Поиск по коду')
#             ),
#         }

# ========== CURRENCY ==========
class CurrencyResource(resources.ModelResource):
    class Meta:
        model = Currency
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = True


@admin.register(Currency)
class CurrencyAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = CurrencyResource

    list_display = (
        'name_colored',
        'code',
        'symbol_display',
        'sorting_order',
        'is_active_badge',
    )
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'symbol')
    ordering = ('sorting_order', 'code')
    list_editable = ('sorting_order',)

    fieldsets = (
        (None, {
            'fields': (
                ('name', 'code'),
                ('symbol', 'sorting_order'),
                'is_active',
            )
        }),
        (_('Дополнительно'), {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Валюта'), ordering='name')
    def name_colored(self, obj):
        colors = {
            'RUB': 'green',
            'USD': 'green',
            'EUR': 'blue',
            'CNY': 'red',
        }
        color = colors.get(obj.code, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.name
        )

    @admin.display(description=_('Символ'))
    def symbol_display(self, obj):
        return obj.symbol or '-'

    @admin.display(description=_('Статус'), boolean=True)
    def is_active_badge(self, obj):
        return obj.is_active


# ========== PRICE VARIETY ==========
class PriceVarietyResource(resources.ModelResource):
    class Meta:
        model = PriceVariety
        import_id_fields = ('code',)
        skip_unchanged = True
        report_skipped = True


@admin.register(PriceVariety)
class PriceVarietyAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = PriceVarietyResource

    list_display = (
        'name',
        'code',
        'sorting_order',
        'is_active_badge',
    )
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'description')
    ordering = ('sorting_order', 'name')
    list_editable = ('sorting_order', )

    fieldsets = (
        (None, {
            'fields': (
                ('name', 'code'),
                'sorting_order',
                'is_active',
            )
        }),
        (_('Описание'), {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description=_('Статус'), boolean=True)
    def is_active_badge(self, obj):
        return obj.is_active

    @admin.display(description=_('Цен'))
    def price_count(self, obj):
        count = obj.pricehistory_set.count()
        url = f'/admin/price/pricehistory/?price_variety__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)


# ========== PRICE HISTORY ==========
class PriceHistoryResource(resources.ModelResource):
    class Meta:
        model = PriceHistory
        import_id_fields = ('name', 'code', 'price_date')
        skip_unchanged = True
        report_skipped = True


@admin.register(PriceHistory)
class PriceHistoryAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = PriceHistoryResource

    list_display = (
        # NameFilter,      # <-- текстовый фильтр названия
        # CodeFilter,      # <-- текстовый фильтр кода
        'name',
        'code',
        'price_display',
        'price_variety',
        'price_date',
        'is_active_badge',
    )
    list_filter = (
        'price_variety',
        'currency',
        'is_active',
        ('price_date', DateRangeFilter),
    )
    search_fields = ('name', 'code', 'description')  # <-- ЭТО ДЛЯ СПИСКА АДМИНКИ
    date_hierarchy = 'price_date'
    ordering = ('-price_date', 'sorting_order')
    list_per_page = 25

    fieldsets = (
        (None, {
            'fields': (
                ('name', 'code'),
                ('price_variety', 'currency'),
                ('price', 'price_date'),
                'sorting_order',
                'is_active',
            )
        }),
        (_('Комментарий'), {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )

    list_select_related = ('price_variety', 'currency')

    @admin.display(description=_('Цена'), ordering='price')
    def price_display(self, obj):
        currency_symbol = obj.currency.symbol if obj.currency else ''
        return f"{obj.price:,.2f} {currency_symbol}".replace(',', ' ')

    @admin.display(description=_('Статус'), boolean=True)
    def is_active_badge(self, obj):
        return obj.is_active

    actions = ['make_active', 'make_inactive', 'copy_price']

    @admin.action(description=_("Активировать выбранные"))
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _("Активировано: {}").format(updated))

    @admin.action(description=_("Деактивировать выбранные"))
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _("Деактивировано: {}").format(updated))

    @admin.action(description=_("Копировать цену на другую дату"))
    def copy_price(self, request, queryset):
        if 'apply' in request.POST:
            new_date = request.POST.get('new_date')
            if new_date:
                count = 0
                for price in queryset:
                    price.pk = None
                    price.price_date = new_date
                    price.save()
                    count += 1
                self.message_user(request, f"Создано копий: {count}")
                return

        context = {
            'title': _("Копировать цены"),
            'queryset': queryset,
            'action': 'copy_price',
            'opts': self.model._meta,
        }
        return render(request, 'admin/pricehistory_copy_intermediate.html', context)