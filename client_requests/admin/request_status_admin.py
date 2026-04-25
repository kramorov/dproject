#client_requests/admin/request_status_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from client_requests.models.request_status import ClientRequestStatus


@admin.register(ClientRequestStatus)
class ClientRequestStatusAdmin(admin.ModelAdmin) :
    """
    Админ-класс для статусов запросов клиентов
    """
    list_display = [
        'name' ,
        'code' ,
        'sorting_order' ,
        'is_active'
    ]

    list_filter = [
        'is_active' ,
    ]

    search_fields = [
        'name' ,
        'code' ,
        'description'
    ]

    list_editable = [
        'sorting_order' ,
        'is_active'
    ]

    fieldsets = (
        (_('Основная информация') , {
            'fields' : (
                'name' ,
                'code' ,
                'description' ,
            )
        }) ,
        (_('Настройки отображения') , {
            'fields' : (
                'sorting_order' ,
                'is_active' ,
            )
        }) ,
    )

