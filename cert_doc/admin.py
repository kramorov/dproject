# cert_doc/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import CertVariety , CertData
from core.admin import BaseAdmin


@admin.register(CertVariety)
class CertVarietyAdmin(BaseAdmin) :
    """
    Админка для типов сертификатов
    """
    list_display = [
        'code' ,
        'name' ,
        'active_badge' ,
        'sorting_order' ,
        'cert_count' ,
        'created_at_short'
    ]

    list_display_links = ['code' , 'name']

    list_filter = [
        'is_active' ,
        ('created_at' , admin.DateFieldListFilter) ,
    ]

    search_fields = [
        'code' ,
        'name' ,
        'description' ,
    ]

    fieldsets = (
        ('Основная информация' , {
            'fields' : ('code' , 'name' , 'description')
        }) ,
        ('Системная информация' , {
            'fields' : ('sorting_order' , 'is_active') ,
            'classes' : ('collapse' ,) ,
        }) ,
    )

    actions = ['activate_selected' , 'deactivate_selected']

    def get_queryset(self , request) :
        """Оптимизируем запросы"""
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('certdata_set')

    def active_badge(self , obj) :
        """Отображение статуса активности"""
        if obj.is_active :
            return format_html(
                '<span style="background: #4CAF50; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-size: 12px;">Активен</span>'
            )
        return format_html(
            '<span style="background: #f44336; color: white; padding: 3px 8px; '
            'border-radius: 10px; font-size: 12px;">Неактивен</span>'
        )

    active_badge.short_description = 'Статус'
    active_badge.admin_order_field = 'is_active'

    def cert_count(self , obj) :
        """Количество сертификатов этого типа"""
        count = obj.certdata_set.count()
        url = reverse('admin:cert_doc_certdata_changelist')
        url += f'?cert_variety__id__exact={obj.id}'

        return format_html(
            '<a href="{}" style="text-decoration: none;">'
            '<span style="background: #2196F3; color: white; padding: 2px 8px; '
            'border-radius: 10px; font-size: 12px;">{}</span>'
            '</a>' ,
            url ,
            count
        )

    cert_count.short_description = 'Сертификаты'

    def created_at_short(self , obj) :
        """Короткая дата создания"""
        return obj.created_at.strftime('%d.%m.%Y')

    created_at_short.short_description = 'Создан'
    created_at_short.admin_order_field = 'created_at'

    @admin.action(description=_('Активировать выбранные'))
    def activate_selected(self , request , queryset) :
        updated = queryset.update(is_active=True)
        self.message_user(
            request ,
            f'Активировано {updated} типов сертификатов.'
        )

    @admin.action(description=_('Деактивировать выбранные'))
    def deactivate_selected(self , request , queryset) :
        updated = queryset.update(is_active=False)
        self.message_user(
            request ,
            f'Деактивировано {updated} типов сертификатов.'
        )


@admin.register(CertData)
class CertDataAdmin(BaseAdmin) :
    """
    Админка для сертификатов
    """
    list_display = [
        'code' ,
        'name' ,
        'cert_variety_link' ,
        'validity_status' ,
        'brand_link' ,
        'attachments_badge' ,
        'is_active_display' ,
        'sorting_order' ,
    ]

    list_display_links = ['code' , 'name']

    list_filter = [
        'is_active' ,
        'cert_variety' ,
        'brand' ,
        ('valid_until' , admin.DateFieldListFilter) ,
        ('created_at' , admin.DateFieldListFilter) ,
    ]

    search_fields = [
        'code' ,
        'name' ,
        'description' ,
        'issued_by' ,
        'cert_variety__name' ,
        'cert_variety__code' ,
        'brand__name' ,
    ]

    filter_horizontal = []

    readonly_fields = BaseAdmin.readonly_fields + [
        'relations_list' ,
        'validity_check' ,
        'download_links' ,
    ]

    fieldsets = (
        ('Основная информация' , {
            'fields' : (
                'name' ,
                'code' ,
                'description' ,
                'cert_variety' ,
            )
        }) ,
        ('Детали сертификата' , {
            'fields' : (
                'issued_by' ,
                'valid_from' ,
                'valid_until' ,
            ) ,
            'classes' : ('wide' ,) ,
        }) ,
        ('Привязки' , {
            'fields' : (
                'brand' ,
                'public_url' ,
                'media_item' ,
            )
        }) ,
        ('Связанные объекты' , {
            'fields' : ('relations_list' ,) ,
            'classes' : ('collapse' ,) ,
        }) ,
        ('Системная информация' , {
            'fields' : ('sorting_order' , 'is_active') ,
            'classes' : ('collapse' ,) ,
        }) ,
        ('Предпросмотр данных' , {
            'fields' : ('data_preview' , 'json_preview') ,
            'classes' : ('collapse' , 'wide') ,
        }) ,
    )

    actions = [
        'mark_as_expired' ,
        'copy_selected' ,
        'export_selected' ,
        'activate_selected' ,
        'deactivate_selected' ,
    ]

    def get_queryset(self , request) :
        """Оптимизируем запросы"""
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'cert_variety' ,
            'brand' ,
            'media_item'
        ).prefetch_related(
            'productcertrelation_relations' ,
            'projectcertrelation_relations' ,
        )

    # Кастомные методы для list_display

    def cert_variety_link(self , obj) :
        """Ссылка на тип сертификата"""
        if obj.cert_variety :
            url = reverse(
                'admin:cert_doc_certvariety_change' ,
                args=[obj.cert_variety.id]
            )
            return format_html(
                '<a href="{}">{}</a>' ,
                url ,
                obj.cert_variety.name or obj.cert_variety.code
            )
        return '-'

    cert_variety_link.short_description = 'Тип'
    cert_variety_link.admin_order_field = 'cert_variety__name'

    def validity_status(self , obj) :
        """Статус действия сертификата"""
        from datetime import date

        if not obj.valid_until :
            return format_html(
                '<span style="background: #757575; color: white; padding: 2px 8px; '
                'border-radius: 10px; font-size: 11px;">Без срока</span>'
            )

        today = date.today()
        days_left = (obj.valid_until - today).days

        if days_left < 0 :
            # Просрочен
            return format_html(
                '<span style="background: #f44336; color: white; padding: 2px 8px; '
                'border-radius: 10px; font-size: 11px; font-weight: bold;">'
                'Просрочен {} дн.</span>' ,
                abs(days_left)
            )
        elif days_left < 30 :
            # Скоро истекает
            return format_html(
                '<span style="background: #FF9800; color: white; padding: 2px 8px; '
                'border-radius: 10px; font-size: 11px;">'
                'Истекает через {} дн.</span>' ,
                days_left
            )
        else :
            # Действует
            return format_html(
                '<span style="background: #4CAF50; color: white; padding: 2px 8px; '
                'border-radius: 10px; font-size: 11px;">'
                'Действует до {}</span>' ,
                obj.valid_until.strftime('%d.%m.%y')
            )

    validity_status.short_description = 'Статус'
    validity_status.admin_order_field = 'valid_until'

    def brand_link(self , obj) :
        """Ссылка на бренд"""
        if obj.brand :
            # Предполагаем, что у Brand есть админка в producers
            try :
                url = reverse(
                    'admin:producers_brand_change' ,
                    args=[obj.brand.id]
                )
                return format_html('<a href="{}">{}</a>' , url , obj.brand.name)
            except :
                return obj.brand.name
        return '-'

    brand_link.short_description = 'Бренд'
    brand_link.admin_order_field = 'brand__name'

    def attachments_badge(self , obj) :
        """Индикатор вложений"""
        badges = []

        if obj.public_url :
            badges.append(
                '<span style="background: #2196F3; color: white; padding: 1px 6px; '
                'border-radius: 10px; font-size: 10px; margin-right: 2px;">URL</span>'
            )

        if obj.media_item and obj.media_item.media_file :
            badges.append(
                '<span style="background: #9C27B0; color: white; padding: 1px 6px; '
                'border-radius: 10px; font-size: 10px; margin-right: 2px;">Файл</span>'
            )

        if not badges :
            return format_html(
                '<span style="color: #999; font-size: 11px;">Нет вложений</span>'
            )

        return mark_safe(''.join(badges))

    attachments_badge.short_description = 'Вложения'

    def is_active_display(self , obj) :
        """Отображение активности"""
        if obj.is_active :
            return format_html(
                '<span style="color: #4CAF50; font-weight: bold;">✓</span>'
            )
        return format_html(
            '<span style="color: #f44336; font-weight: bold;">✗</span>'
        )

    is_active_display.short_description = 'Акт.'
    is_active_display.admin_order_field = 'is_active'

    # Методы для fieldsets

    def validity_check(self , obj) :
        """Проверка валидности дат"""
        if not obj.pk :
            return "Сначала сохраните объект"

        errors = []
        warnings = []

        if obj.valid_from and obj.valid_until :
            if obj.valid_from > obj.valid_until :
                errors.append("Дата начала не может быть позже даты окончания")

        if obj.valid_until :
            from datetime import date
            today = date.today()
            if obj.valid_until < today :
                errors.append("Сертификат просрочен!")
            elif (obj.valid_until - today).days < 30 :
                warnings.append("Сертификат скоро истекает")

        html = []
        if errors :
            html.append('<div style="background: #ffebee; padding: 10px; border-radius: 5px; margin: 5px 0;">')
            html.append('<strong style="color: #c62828;">Ошибки:</strong><ul style="margin: 5px 0;">')
            for error in errors :
                html.append(f'<li>{error}</li>')
            html.append('</ul></div>')

        if warnings :
            html.append('<div style="background: #fff3e0; padding: 10px; border-radius: 5px; margin: 5px 0;">')
            html.append('<strong style="color: #ef6c00;">Предупреждения:</strong><ul style="margin: 5px 0;">')
            for warning in warnings :
                html.append(f'<li>{warning}</li>')
            html.append('</ul></div>')

        if not errors and not warnings and (obj.valid_from or obj.valid_until) :
            html.append('<div style="background: #e8f5e8; padding: 10px; border-radius: 5px; margin: 5px 0;">')
            html.append('<span style="color: #2e7d32;">✓ Даты корректны</span>')
            html.append('</div>')

        if not obj.valid_from and not obj.valid_until :
            html.append('<div style="background: #f5f5f5; padding: 10px; border-radius: 5px; margin: 5px 0;">')
            html.append('<span style="color: #757575;">Срок действия не указан</span>')
            html.append('</div>')

        return format_html(''.join(html))

    validity_check.short_description = "Проверка валидности"

    def download_links(self , obj) :
        """Ссылки для скачивания"""
        links = []

        if obj.public_url :
            links.append(
                format_html(
                    '<a href="{}" target="_blank" style="display: inline-block; '
                    'background: #2196F3; color: white; padding: 8px 15px; '
                    'border-radius: 4px; text-decoration: none; margin-right: 10px;">'
                    '📎 Открыть внешнюю ссылку</a>' ,
                    obj.public_url
                )
            )

        if obj.media_item and obj.media_item.media_file :
            links.append(
                format_html(
                    '<a href="{}" target="_blank" style="display: inline-block; '
                    'background: #9C27B0; color: white; padding: 8px 15px; '
                    'border-radius: 4px; text-decoration: none;">'
                    '📁 Скачать файл ({})</a>' ,
                    obj.media_item.media_file.url ,
                    obj.media_item.get_file_extension() if hasattr(obj.media_item , 'get_file_extension') else 'файл'
                )
            )

        if not links :
            return format_html(
                '<div style="color: #999; padding: 10px; background: #f5f5f5; '
                'border-radius: 5px;">Нет доступных файлов для скачивания</div>'
            )

        return format_html('<div style="margin: 10px 0;">{}</div>' , mark_safe(''.join(links)))

    download_links.short_description = "Ссылки для скачивания"

    def relations_list(self , obj) :
        """Список связанных объектов"""
        if not obj.pk :
            return "Сначала сохраните объект"

        html = ['<div style="max-height: 300px; overflow-y: auto;">']

        # Продукты
        product_relations = obj.productcertrelation_relations.all()
        if product_relations.exists() :
            html.append('<h4 style="margin: 15px 0 5px 0;">📦 Связанные продукты:</h4>')
            html.append('<ul style="margin-left: 20px;">')
            for rel in product_relations[:10] :  # Ограничиваем показ
                product_name = str(rel.product) if rel.product else "Неизвестный продукт"
                html.append(
                    f'<li>'
                    f'<a href="{reverse("admin:cert_doc_productcertrelation_change" , args=[rel.id])}">'
                    f'{product_name}'
                    f'</a>'
                    f'{" <span style=\"color: #4CAF50;\">(основной)</span>" if rel.is_primary else ""}'
                    f'</li>'
                )
            if product_relations.count() > 10 :
                html.append(f'<li>... и еще {product_relations.count() - 10}</li>')
            html.append('</ul>')

        # Проекты
        project_relations = obj.projectcertrelation_relations.all()
        if project_relations.exists() :
            html.append('<h4 style="margin: 15px 0 5px 0;">🏗️ Связанные проекты:</h4>')
            html.append('<ul style="margin-left: 20px;">')
            for rel in project_relations[:10] :
                project_name = str(rel.project) if rel.project else "Неизвестный проект"
                html.append(
                    f'<li>'
                    f'<a href="{reverse("admin:cert_doc_projectcertrelation_change" , args=[rel.id])}">'
                    f'{project_name}'
                    f'</a>'
                    f'</li>'
                )
            if project_relations.count() > 10 :
                html.append(f'<li>... и еще {project_relations.count() - 10}</li>')
            html.append('</ul>')

        if not product_relations.exists() and not project_relations.exists() :
            html.append(
                '<div style="color: #999; padding: 15px; background: #f5f5f5; '
                'border-radius: 5px; text-align: center;">'
                'Нет связанных объектов'
                '</div>'
            )

        html.append('</div>')

        return format_html(''.join(html))

    relations_list.short_description = "Связанные объекты"

    # Действия

    @admin.action(description=_('Пометить как просроченные'))
    def mark_as_expired(self , request , queryset) :
        """Пометить сертификаты как просроченные (установить is_active=False)"""
        from datetime import date
        today = date.today()

        updated = 0
        for cert in queryset :
            if cert.valid_until and cert.valid_until < today :
                cert.is_active = False
                cert.save()
                updated += 1

        self.message_user(
            request ,
            f'Помечено как просроченные: {updated} сертификатов.'
        )

    @admin.action(description=_('Копировать выбранные'))
    def copy_selected(self , request , queryset) :
        """Создать копии выбранных сертификатов"""
        copied = 0
        for cert in queryset :
            # Создаем копию
            cert.pk = None
            cert.code = f"{cert.code}_copy" if cert.code else None
            cert.name = f"{cert.name} (копия)" if cert.name else None
            cert.sorting_order = 999  # В конец списка
            cert.save()
            copied += 1

        self.message_user(
            request ,
            f'Создано {copied} копий сертификатов.'
        )

    @admin.action(description=_('Экспортировать выбранные'))
    def export_selected(self , request , queryset) :
        """Экспорт сертификатов (заглушка для примера)"""
        self.message_user(
            request ,
            f'Готовится экспорт {queryset.count()} сертификатов...'
        )
        # Здесь можно реализовать экспорт в Excel/PDF

    @admin.action(description=_('Активировать выбранные'))
    def activate_selected(self , request , queryset) :
        updated = queryset.update(is_active=True)
        self.message_user(
            request ,
            f'Активировано {updated} сертификатов.'
        )

    @admin.action(description=_('Деактивировать выбранные'))
    def deactivate_selected(self , request , queryset) :
        updated = queryset.update(is_active=False)
        self.message_user(
            request ,
            f'Деактивировано {updated} сертификатов.'
        )

    class Media :
        css = {
            'all' : (
                'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css' ,
            )
        }
