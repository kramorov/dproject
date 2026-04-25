#client_requests/admin/request_number_counter_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from ..models import RequestNumberCounter


@admin.register(RequestNumberCounter)
class RequestNumberCounterAdmin(admin.ModelAdmin) :
    list_display = [
        'project_customer' ,
        'project_customer_user' ,
        'project_customer_request_number' ,
        'project_customer_user_request_number'
    ]

    list_filter = [
        'project_customer'
    ]

    search_fields = [
        'project_customer__name' ,
        'project_customer_user__last_name' ,
        'project_customer_user__first_name'
    ]

    readonly_fields = [
        'project_customer_request_number' ,
        'project_customer_user_request_number'
    ]

    fieldsets = (
        (_('Компания') , {
            'fields' : ('project_customer' ,)
        }) ,
        (_('Пользователь') , {
            'fields' : ('project_customer_user' ,)
        }) ,
        (_('Счетчики') , {
            'fields' : ('project_customer_request_number' , 'project_customer_user_request_number')
        }) ,
    )