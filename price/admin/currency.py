# price/admin/currency.py

from django.shortcuts import render, redirect
import pandas as pd
from datetime import datetime, date

from django.contrib import admin
from django.http import Http404
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from import_export.admin import ImportExportModelAdmin
from import_export import resources
from rangefilter.filters import DateRangeFilter


from price.models.currency import Currency, PriceVariety, PriceHistory

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
class PriceHistoryAdmin(admin.ModelAdmin):
    resource_class = PriceHistoryResource

    list_display = (
        # NameFilter,      # <-- текстовый фильтр названия
        # CodeFilter,      # <-- текстовый фильтр кода
        'name',
        'code',
        'price_display',
        'price_variety',
        'price_date',
        'view_details_button',  # <-- ДОБАВИТЬ
        'is_active_badge',
    )
    change_list_template = 'admin/price/pricehistory/change_list_popup.html'

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
                ('price', 'price_date'),  # только поля модели
                ('sorting_order', 'is_active'),
            )
        }),
        (_('Комментарий'), {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )

    list_select_related = ('price_variety', 'currency')

    @admin.display(description=_('Подробнее'))
    def view_details_button(self, obj):
        url = reverse('admin:price_history_details_popup', args=[obj.id])
        return format_html(
            '<button type="button" class="button details-button" data-url="{}" '
            'style="background: #79aec8; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">'
            '🔍 Подробнее</button>',
            url
        )

    def price_details_popup(self, request, price_id):
        """Popup с детальной информацией о цене"""
        try:
            # Проверяем, что объект существует
            price = PriceHistory.objects.select_related(
                'price_variety', 'currency'
            ).get(id=price_id)

            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Price found: {price.id}, {price.name}")

            context = {
                'price': price,
                'converted': price.get_converted_prices(),
                'is_popup': True,
            }

            response = render(request, 'admin/price/pricehistory/details_popup.html', context)
            response['X-Frame-Options'] = 'SAMEORIGIN'
            return response

        except PriceHistory.DoesNotExist:
            logger.error(f"Price not found: {price_id}")
            raise Http404('Цена не найдена')
        except Exception as e:
            logger.error(f"Error in price_details_popup: {e}", exc_info=True)
            raise

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-excel/',
                 self.admin_site.admin_view(self.import_excel_view),
                 name='price_history_import_excel'),
            path('<int:price_id>/details-popup/',
                 self.admin_site.admin_view(self.price_details_popup),
                 name='price_history_details_popup'),
        ]
        return custom_urls + urls

    def price_with_currency(self, obj):
        return format_html(
            '{} {}',
            obj.price,
            obj.currency.symbol if obj.currency else ''
        )

    price_with_currency.short_description = 'Цена'

    def description_short(self, obj):
        if obj.description:
            return format_html(
                '<span title="{}">{}</span>',
                obj.description,
                obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
            )
        return '-'

    description_short.short_description = 'Описание'

    @admin.display(description=_('Цена'), ordering='price')
    def price_display(self, obj):
        currency_symbol = obj.currency.symbol if obj.currency else ''
        return f"{obj.price:,.2f} {currency_symbol}".replace(',', ' ')

    @admin.display(description=_('Статус'), boolean=True)
    def is_active_badge(self, obj):
        return obj.is_active

    actions = ['copy_price']  # <-- ДОБАВЬТЕ ЭТУ СТРОКУ
    @admin.action(description=_("Копировать записи с ценой "))

    def copy_price(self, request, queryset):
        if 'apply' in request.POST:
            new_date = request.POST.get('new_date')
            if new_date:
                count = 0
                for price in queryset:
                    # Используем метод модели
                    price.create_copy(new_date)
                    count += 1
                self.message_user(request, f"Создано копий: {count}")
                return

        context = {
            'title': _("Копировать цены"),
            'queryset': queryset,
            'action': 'copy_price',
            'opts': self.model._meta,
            'today': date.today(),  # Добавляем сегодняшнюю дату
        }
        return render(request, 'admin/price/pricehistory/pricehistory_copy_intermediate.html', context)

    def import_excel_view(self, request):
        """View для импорта цен из Excel"""

        if request.method == 'POST':
            # Получаем параметры из формы
            currency_id = request.POST.get('currency')
            price_type_id = request.POST.get('price_type')
            price_date = request.POST.get('price_date')
            excel_file = request.FILES.get('excel_file')
            update_existing = request.POST.get('update_existing') == 'on'

            # Валидация
            if not all([currency_id, price_type_id, excel_file]):
                self.message_user(request, "Заполните все поля", level='ERROR')
                return redirect('admin:price_history_import_excel')

            try:
                # Получаем объекты валюты и типа цены
                currency = Currency.objects.get(id=currency_id)
                price_type = PriceVariety.objects.get(id=price_type_id)

                # Определяем дату импорта
                date_message = ""
                if price_date:
                    import_date = datetime.strptime(price_date, '%Y-%m-%d').date()
                else:
                    import_date = date.today()
                    date_message = f" (использована текущая дата: {import_date.strftime('%d.%m.%Y')})"

                # Читаем Excel
                df = pd.read_excel(excel_file)

                # Проверяем наличие необходимых колонок
                required_columns = ['name', 'price']
                if not all(col in df.columns for col in required_columns):
                    self.message_user(
                        request,
                        "Excel файл должен содержать колонки: name, price",
                        level='ERROR'
                    )
                    return redirect('admin:price_history_import_excel')

                # Статистика импорта
                stats = {
                    'total': len(df),
                    'created': 0,
                    'updated': 0,
                    'skipped': 0,
                    'errors': 0,
                    'no_date_used': 1 if date_message else 0,  # Для статистики
                }

                error_rows = []

                # Импортируем строки
                for idx, row in df.iterrows():
                    try:
                        name = str(row['name']).strip()
                        price_str = str(row['price']).strip()

                        # Очищаем цену
                        price_str = (price_str.replace(' ', '')
                                     .replace(',', '.')
                                     .replace('₽', '')
                                     .replace('$', '')
                                     .replace('€', ''))

                        try:
                            price = float(price_str)
                        except ValueError:
                            stats['skipped'] += 1
                            error_rows.append(idx + 2)
                            continue

                        if not name or pd.isna(price):
                            stats['skipped'] += 1
                            continue

                        code = str(row.get('code', '')).strip() if 'code' in df.columns else None
                        description = str(row.get('description', '')).strip() if 'description' in df.columns else ''

                        # Проверяем существующую запись
                        existing = None
                        if update_existing:
                            existing = PriceHistory.objects.filter(
                                name=name,
                                code=code,
                                price_date=import_date,
                                price_variety=price_type,
                                currency=currency
                            ).first()

                        if existing and update_existing:
                            # Обновляем
                            existing.price = price
                            existing.description = description
                            existing.save()
                            stats['updated'] += 1
                        else:
                            # Создаем новую
                            PriceHistory.objects.create(
                                name=name,
                                code=code if code else None,
                                price=price,
                                currency=currency,
                                price_variety=price_type,
                                price_date=import_date,
                                description=description,
                                is_active=True,
                            )
                            stats['created'] += 1

                    except Exception as e:
                        stats['errors'] += 1
                        error_rows.append(idx + 2)

                # Формируем сообщение о результате
                message_parts = [
                    f"✅ Импорт завершен{date_message}.",
                    f"📊 Всего: {stats['total']}",
                    f"✅ Создано: {stats['created']}",
                    f"🔄 Обновлено: {stats['updated']}",
                    f"⏭️ Пропущено: {stats['skipped']}",
                    f"❌ Ошибок: {stats['errors']}"
                ]

                if date_message:
                    message_parts.insert(1, f"📅 {date_message.strip()}")

                if error_rows:
                    message_parts.append(f"⚠️ Строки с ошибками: {', '.join(map(str, error_rows))}")

                message = "\n".join(message_parts)
                self.message_user(request, message)

            except Exception as e:
                self.message_user(request, f"❌ Ошибка импорта: {e}", level='ERROR')

            return redirect('admin:price_pricehistory_changelist')

        # GET запрос - показываем форму
        context = {
            'title': '📥 Импорт цен из Excel',
            'currencies': Currency.objects.filter(is_active=True),
            'price_types': PriceVariety.objects.filter(is_active=True),
            'today': date.today(),
            'opts': self.model._meta,
        }
        return render(request, 'admin/price/pricehistory/import_excel.html', context)