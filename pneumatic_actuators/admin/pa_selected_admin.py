from django.contrib import admin
from django import forms
from django.utils.html import format_html

from pneumatic_actuators.models.pa_actuator_selected import PneumaticActuatorSelected
from pneumatic_actuators.models.pa_options import PneumaticSafetyPositionOption , PneumaticSpringsQtyOption , \
    PneumaticTemperatureOption , PneumaticIpOption , PneumaticExdOption , PneumaticBodyCoatingOption

@admin.register(PneumaticActuatorSelected)
class PneumaticActuatorSelectedAdmin(admin.ModelAdmin) :
    list_display = [
        'name' , 'code' , 'selected_model_display' ,
        'safety_position_display' , 'springs_qty_display' ,
        'temperature_display' , 'ip_display' , 'exd_display' , 'body_coating_display' ,
        'sorting_order' , 'is_active'
    ]
    list_filter = [
        'is_active' , 'selected_model' ,
        'selected_safety_position__safety_position' ,
        'selected_springs_qty__springs_qty' ,
        'selected_temperature' ,
        'selected_ip__ip_option' ,
        'selected_exd__exd_option' ,
        'selected_body_coating__body_coating_option'
    ]
    search_fields = ['name' , 'code' , 'description']
    # autocomplete_fields = ['selected_model' , 'selected_safety_position' , 'selected_springs_qty']
    fieldsets = (
        ('Основная информация', {
            'fields': (
                ('selected_model', 'name', 'code'),
            )
        }),
        ('Опции привода', {
            'fields': (
                ('selected_safety_position', 'selected_springs_qty', 'selected_temperature'),
                ('selected_ip', 'selected_exd', 'selected_body_coating'),
            ),
        }),
        ('Описание:', {
            'fields': (
                'description',
            ),
        })
    )

    class Media :
        js = ('admin/js/pneumatic_actuator_selected.js' ,)  # новый файл
        css = {
            'all': ('admin/css/pneumatic_admin.css',)  # добавьте эту строку
        }
        # js = ('admin/js/pneumatic_actuator_selected.js' ,)



    def get_form(self , request , obj=None , **kwargs) :
        form = super().get_form(request , obj , **kwargs)
        if obj and obj.selected_model :
            is_da = (obj.selected_model.pneumatic_actuator_variety and
                     obj.selected_model.pneumatic_actuator_variety.code == 'DA')
            if is_da :
                form.base_fields['selected_safety_position'].required = False
        return form


    def get_queryset(self , request) :
        return super().get_queryset(request).select_related(
            'selected_model' ,
            'selected_safety_position__safety_position' ,
            'selected_springs_qty__springs_qty' ,
            'selected_temperature__model_line' ,  # ЕСЛИ НУЖНА СВЯЗЬ С MODEL_LINE
            'selected_ip__model_line' ,
            'selected_exd__model_line' ,
            'selected_body_coating__model_line'
        )

    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     """Минимальная версия - только диагностика"""
    #     print(f"🔧 === formfield_for_foreignkey called. FORM FIELD DEBUG: {db_field.name} ===")
    #
    #     # Делаем все опциональные поля необязательными
    #     if db_field.name in [
    #         'selected_safety_position', 'selected_springs_qty',
    #         'selected_temperature', 'selected_ip', 'selected_exd', 'selected_body_coating'
    #     ]:
    #         kwargs['required'] = False
    #         # Не устанавливаем queryset - пусть JS управляет опциями
    #         kwargs['queryset'] = db_field.related_model.objects.none()
    #
    #     print(f"🔧 formfield_for_foreignkey Field made optional, queryset cleared for JS")
    #     print(f"🔧 formfield_for_foreignkey === END FORM FIELD DEBUG ===")
    #
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)