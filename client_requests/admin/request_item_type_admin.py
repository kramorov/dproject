#client_requests/admin/request_item_type_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from ..models import RequestItemType


@admin.register(RequestItemType)
class RequestItemTypeAdmin(admin.ModelAdmin) :
    list_display = ['name' , 'symbolic_code' , 'sort_order' , 'is_active']
    list_filter = ['is_active' , 'need_valve_selection' , 'need_pneumatic_actuator_selection']
    search_fields = ['name' , 'symbolic_code']
    list_editable = ['sort_order' , 'is_active']

    fieldsets = (
        (_('Основная информация') , {
            'fields' : ('symbolic_code' , 'name' , 'description')
        }) ,
        (_('Что подбирать') , {
            'fields' : (
                ('need_valve_selection' , 'need_pneumatic_actuator_selection') ,
                ('need_electric_actuator_selection' , 'need_mounting_kit') ,
                ('need_fittings' , 'need_positioner') ,
                ('need_air_preparation' ,) ,
            )
        }) ,
        (_('Настройки') , {
            'fields' : ('sort_order' , 'is_active')
        }) ,
    )