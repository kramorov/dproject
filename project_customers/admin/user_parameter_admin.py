# user_parameter_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from ..models.user_parameter import UserParameter


@admin.register(UserParameter)
class UserParameterAdmin(admin.ModelAdmin) :
    list_display = ['user' , 'name' , 'code' , 'value_preview' , 'is_system']
    list_filter = ['is_system' , 'user']
    search_fields = ['user__last_name' , 'user__first_name' , 'name' , 'code' , 'value']

    fieldsets = (
        (_('Пользователь') , {
            'fields' : ('user' ,)
        }) ,
        (_('Параметр') , {
            'fields' : ('name' , 'code' , 'value' , 'is_system' , 'description')
        }) ,
    )

    def value_preview(self , obj) :
        """Предпросмотр значения"""
        if len(obj.value) > 50 :
            return obj.value[:50] + '...'
        return obj.value or '-'

    value_preview.short_description = _("Значение")