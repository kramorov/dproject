#client_requests/admin/client_request_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.html import format_html

from project_customers.utils import get_current_customer_user
from ..models import ClientRequest


@admin.register(ClientRequest)
class ClientRequestAdmin(admin.ModelAdmin) :
    list_display = [
        'code' ,
        'name' ,
        'request_status' ,
        'request_date' ,
        'request_from_client_company' ,
        'orders_1c_preview' ,
        'bitrix_deal_id' ,
        'items_count'
    ]

    list_filter = [
        'request_status' ,
        'request_date' ,
        'request_from_client_company'
    ]

    search_fields = [
        'code' ,
        'name' ,
        'client_request_number' ,
        'request_text' ,
        'orders_1c' ,
        'bitrix_deal_id'
    ]

    readonly_fields = [
        'code' ,
        'created_at' ,
        'updated_at' ,
        'items_link'
    ]

    fieldsets = (
        (_('Номер и статус') , {
            'fields' : ('code' , 'client_request_number' , 'name' , 'request_status')
        }) ,
        (_('Клиент') , {
            'fields' : ('request_from_client_company' , 'request_responsible_person' , 'end_customer')
        }) ,
        (_('Содержание') , {
            'fields' : ('request_text' , 'internal_notes')
        }) ,
        (_('Даты') , {
            'fields' : ('request_date' , 'required_by_date')
        }) ,
        (_('Интеграции') , {
            'fields' : ('orders_1c' , 'bitrix_deal_id')
        }) ,
        (_('Позиции') , {
            'fields' : ('items_link' ,)
        }) ,
        (_('Системное') , {
            'fields' : ('created_at' , 'updated_at') ,
            'classes' : ('collapse' ,)
        }) ,
    )

    def orders_1c_preview(self , obj) :
        """Предпросмотр заказов в 1С"""
        if obj.orders_1c :
            return obj.onec_orders[:50] + '...' if len(obj.onec_orders) > 50 else obj.onec_orders
        return '-'

    orders_1c_preview.short_description = _("Заказы в 1С")

    def items_link(self , obj) :
        """Ссылка на позиции заявки"""
        count = obj.request_lines.filter(is_current=True).count()
        url = reverse('admin:client_requests_clientrequestitem_changelist')
        return format_html('<a href="{}?request_parent__id__exact={}">{} позиций</a>' , url , obj.id , count)

    items_link.short_description = _("Позиции")

    def items_count(self , obj) :
        return obj.request_lines.filter(is_current=True).count()

    items_count.short_description = _("Позиций")

    actions = ['duplicate_request']

    @admin.action(description=_("Копировать заявку"))
    def duplicate_request(self , request , queryset) :
        for obj in queryset :
            # Создаем копию
            obj.pk = None
            obj.code = ''
            obj.save()

    def save_model(self , request , obj , form , change) :
        if not change :
            # Устанавливаем владельца из сессии
            customer_user = get_current_customer_user(request)

            if customer_user :
                obj.project_customer_user_request_owner = customer_user
                obj.project_customer_request_owner = customer_user.customer

        super().save_model(request , obj , form , change)

    def get_queryset(self , request) :
        qs = super().get_queryset(request)
        customer_user = get_current_customer_user(request)
        if customer_user :
            # Показываем только заявки, принадлежащие этой компании
            return qs.filter(project_customer_request_owner=customer_user.customer)
        return qs