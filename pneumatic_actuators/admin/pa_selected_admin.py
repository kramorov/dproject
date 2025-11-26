from django.contrib import admin
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
        ('Основная информация' , {
            'fields' : (
                'selected_model' ,
                'is_active' ,
                'sorting_order'
            )
        }) ,
        ('Опции привода' , {
            'fields' : (
                'selected_safety_position' ,
                'selected_springs_qty' ,
            )
        }) ,
        ('Дополнительные опции' , {
            'fields' : (
                'selected_temperature' ,
                'selected_ip' ,
                'selected_exd' ,
                'selected_body_coating' ,
            ) ,
            'classes' : ('collapse' ,)
        }) ,
        ('Автоматически генерируемые поля' , {
            'fields' : (
                'name' ,
                'code' ,
                'description' ,
            ) ,
            'classes' : ('collapse' ,)
        })
    )

    class Media :
        js = ('admin/js/pneumatic_admin.js' ,)  # новый файл
        # js = ('admin/js/pneumatic_actuator_selected.js' ,)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Добавляем API endpoint для JavaScript
        form.api_url = '/admin/pneumatic_actuators/api/options/'
        return form

    # def selected_model_display(self , obj) :
    #     return obj.selected_model.name if obj.selected_model else "-"
    #
    # selected_model_display.short_description = "Модель"
    #
    # def safety_position_display(self , obj) :
    #     if obj.selected_safety_position :
    #         return f"{obj.selected_safety_position.safety_position.name} ({obj.selected_safety_position.encoding})"
    #     return "-"
    #
    # safety_position_display.short_description = "Положение безопасности"
    #
    # def springs_qty_display(self , obj) :
    #     if obj.selected_springs_qty :
    #         return f"{obj.selected_springs_qty.springs_qty.name} ({obj.selected_springs_qty.encoding})"
    #     return "-"
    #
    # springs_qty_display.short_description = "Количество пружин"

    # НОВЫЕ МЕТОДЫ ДЛЯ ОТОБРАЖЕНИЯ
    # def temperature_display(self , obj) :
    #     if obj.selected_temperature :
    #         return f"{obj.selected_temperature.get_display_name()} ({obj.selected_temperature.encoding})"  # ИСПОЛЬЗУЕМ МЕТОД МОДЕЛИ
    #     return "-"
    #
    # temperature_display.short_description = "Температура"
    #
    # def ip_display(self , obj) :
    #     if obj.selected_ip :
    #         return f"{obj.selected_ip.ip_option.name} ({obj.selected_ip.encoding})"  # ЕСТЬ ip_option
    #     return "-"
    #
    # ip_display.short_description = "IP защита"
    #
    # def exd_display(self , obj) :
    #     if obj.selected_exd :
    #         return f"{obj.selected_exd.exd_option.name} ({obj.selected_exd.encoding})"  # ЕСТЬ exd_option
    #     return "-"
    #
    # exd_display.short_description = "Взрывозащита"
    #
    # def body_coating_display(self , obj) :
    #     if obj.selected_body_coating :
    #         return f"{obj.selected_body_coating.body_coating_option.name} ({obj.selected_body_coating.encoding})"
    #     return "-"
    #
    # body_coating_display.short_description = "Покрытие"

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

    def formfield_for_foreignkey(self , db_field , request , **kwargs) :
        """Фильтрация опций в зависимости от выбранной модели"""
        if db_field.name in [
            'selected_safety_position' , 'selected_springs_qty' ,
            'selected_temperature' , 'selected_ip' , 'selected_exd' , 'selected_body_coating'
        ] :
            obj_id = request.resolver_match.kwargs.get('object_id')
            print(f"=== DEBUG: obj_id={obj_id}, db_field={db_field.name}")  # ДОБАВЬ ЭТУ СТРОКУ
            if obj_id :
                try :
                    obj = self.get_queryset(request).get(pk=obj_id)
                    print(f"=== DEBUG: selected_model={obj.selected_model}")  # ДОБАВЬ ЭТУ СТРОКУ
                    if obj.selected_model :
                        if db_field.name == 'selected_safety_position' :
                            kwargs["queryset"] = PneumaticSafetyPositionOption.objects.filter(
                                model_line_item=obj.selected_model ,  # ПРЯМАЯ СВЯЗЬ
                                is_active=True
                            )
                            print(f"=== DEBUG: Safety options count: {kwargs['queryset'].count()}")
                        elif db_field.name == 'selected_springs_qty' :
                            kwargs["queryset"] = PneumaticSpringsQtyOption.objects.filter(
                                model_line_item=obj.selected_model ,  # ПРЯМАЯ СВЯЗЬ
                                is_active=True
                            )
                        elif db_field.name == 'selected_temperature' and obj.selected_model.model_line :
                            kwargs["queryset"] = PneumaticTemperatureOption.objects.filter(
                                model_line=obj.selected_model.model_line ,  # ЧЕРЕЗ MODEL_LINE
                                is_active=True
                            )
                        elif db_field.name == 'selected_ip' and obj.selected_model.model_line :
                            kwargs["queryset"] = PneumaticIpOption.objects.filter(
                                model_line=obj.selected_model.model_line ,
                                is_active=True
                            )
                        elif db_field.name == 'selected_exd' and obj.selected_model.model_line :
                            kwargs["queryset"] = PneumaticExdOption.objects.filter(
                                model_line=obj.selected_model.model_line ,
                                is_active=True
                            )
                        elif db_field.name == 'selected_body_coating' and obj.selected_model.model_line :
                            kwargs["queryset"] = PneumaticBodyCoatingOption.objects.filter(
                                model_line=obj.selected_model.model_line ,
                                is_active=True
                            )
                except PneumaticActuatorSelected.DoesNotExist :
                    print("=== DEBUG: Object does not exist")
                    pass

        return super().formfield_for_foreignkey(db_field , request , **kwargs)