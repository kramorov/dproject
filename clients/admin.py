from django.contrib import admin
from .models import Company, CompanyPerson
from django.utils.translation import gettext_lazy as _

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin) :
    list_display = ('id', 'name', 'full_name','code', 'is_active' , 'sorting_order')
    list_filter = ('is_active' ,)
    list_editable = ('name', 'full_name','code','sorting_order' , 'is_active')

    fieldsets = (
        (_('Основная информация') , {
            'fields' : (

                'full_name' ,
                'code' ,
                'description' ,
            )
        }) ,
        (_('Отображение') , {
            'fields' : (
                'sorting_order' ,
                'is_active' ,
            )
        }) ,
        (_('Интеграции') , {
            'fields' : ('partner_1c' , 'bitrix_id')
        }) ,
        (_('Владельцы') , {
            'fields' : (
                'project_customer_request_owner' ,
                'project_customer_user_request_owner' ,
            ) ,
            'classes' : ('collapse' ,) ,
            'description' : _('Настройки для фильтрации и доступа')
        }) ,
    )


@admin.register(CompanyPerson)
class CompanyPersonAdmin(admin.ModelAdmin) :
    list_display = (
        'id',
        'name',
        'full_name',
        'employee_company' ,
        'person_email' ,
        'is_active'
    )
    list_filter = ('employee_company' , 'is_active')
    list_editable = (
        'name',
        'full_name',
        'employee_company' ,
        'person_email' ,
        'is_active'
    )

    fieldsets = (
        (_('Основная информация') , {
            'fields' : (
                'name',
                'full_name' ,
                'employee_company' ,
                'is_active' ,
            )
        }) ,
        (_('Контакты') , {
            'fields' : (
                'phone_number_office' ,
                'phone_number_cell' ,
                'person_email' ,
            )
        }) ,
        (_('Интеграции') , {
            'fields' : (
                'partner_1c' ,
                'bitrix_id' ,
            ) ,
            'classes' : ('collapse' ,) ,
        }) ,
        (_('Системное') , {
            'fields' : (
                'code' ,
                'description' ,
                'sorting_order' ,
            ) ,
            'classes' : ('collapse' ,) ,
        }) ,
    )

