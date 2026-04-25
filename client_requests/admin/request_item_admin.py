#client_requests/admin/request_item_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from ..models import ClientRequestItem


@admin.register(ClientRequestItem)
class ClientRequestItemAdmin(admin.ModelAdmin) :
    list_display = [
        'request_parent' ,
        'item_no' ,
        'item_type' ,
        'version' ,
        'is_current' ,
        'status' ,
        'changed_at'
    ]

    list_filter = [
        'is_current' ,
        'status' ,
        'item_type' ,
        'changed_at'
    ]

    search_fields = [
        'request_parent__request_number' ,
        'request_line_text' ,
        'request_line_ol'
    ]

    readonly_fields = [
        'version' ,
        'is_current' ,
        'changed_at' ,
        'parent_version'
    ]

    fieldsets = (
        (_('Заявка') , {
            'fields' : ('request_parent' ,)
        }) ,
        (_('Позиция') , {
            'fields' : ('item_no' , 'item_type' , 'status')
        }) ,
        (_('Исходные данные') , {
            'fields' : ('request_line_text' , 'request_line_ol' , 'source_request_line_number')
        }) ,
        (_('Версионирование') , {
            'fields' : ('version' , 'is_current' , 'parent_version' , 'change_comment' , 'changed_by' , 'changed_at')
        }) ,
    )

    def get_queryset(self , request) :
        return super().get_queryset(request).select_related(
            'request_parent' , 'item_type' , 'parent_version' , 'changed_by'
        )