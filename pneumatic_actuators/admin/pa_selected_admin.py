from django.contrib import admin
from django.utils.html import format_html

from pneumatic_actuators.models.pa_actuator_selected import PneumaticActuatorSelected
from pneumatic_actuators.models.pa_options import PneumaticSafetyPositionOption , PneumaticSpringsQtyOption


@admin.register(PneumaticActuatorSelected)
class PneumaticActuatorSelectedAdmin(admin.ModelAdmin) :
    list_display = [
        'name' , 'code' , 'selected_model_display' ,
        'safety_position_display' , 'springs_qty_display' ,
        'sorting_order' , 'is_active'
    ]
    list_filter = [
        'is_active' , 'selected_model' ,
        'selected_safety_position__safety_position' ,
        'selected_springs_qty__springs_qty'
    ]
    search_fields = ['name' , 'code' , 'description']
    # autocomplete_fields = ['selected_model' , 'selected_safety_position' , 'selected_springs_qty']
    fieldsets = (
        ('Основная информация' , {
            'fields' : (
                'selected_model' ,
                'selected_safety_position' ,
                'selected_springs_qty' ,
                'is_active' ,
                'sorting_order'
            )
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

    def selected_model_display(self , obj) :
        return obj.selected_model.name if obj.selected_model else "-"

    selected_model_display.short_description = "Модель"

    def safety_position_display(self , obj) :
        if obj.selected_safety_position :
            return f"{obj.selected_safety_position.safety_position.name} ({obj.selected_safety_position.encoding})"
        return "-"

    safety_position_display.short_description = "Положение безопасности"

    def springs_qty_display(self , obj) :
        if obj.selected_springs_qty :
            return f"{obj.selected_springs_qty.springs_qty.name} ({obj.selected_springs_qty.encoding})"
        return "-"

    springs_qty_display.short_description = "Количество пружин"

    def get_queryset(self , request) :
        return super().get_queryset(request).select_related(
            'selected_model' ,
            'selected_safety_position__safety_position' ,
            'selected_springs_qty__springs_qty'
        )

    def formfield_for_foreignkey(self , db_field , request , **kwargs) :
        """Фильтрация опций в зависимости от выбранной модели"""
        if db_field.name in ['selected_safety_position' , 'selected_springs_qty'] :
            # Получаем текущий объект из запроса
            obj_id = request.resolver_match.kwargs.get('object_id')
            if obj_id :
                try :
                    obj = self.get_queryset(request).get(pk=obj_id)
                    if obj.selected_model :
                        # ФИЛЬТР ПО КОНКРЕТНОЙ МОДЕЛИ
                        filter_kwargs = {
                            'model_line_item' : obj.selected_model ,  # ← ИМЕННО ЭТА СТРОКА
                            'is_active' : True
                        }

                        if db_field.name == 'selected_safety_position' :
                            kwargs["queryset"] = PneumaticSafetyPositionOption.objects.filter(
                                **filter_kwargs
                            )
                        elif db_field.name == 'selected_springs_qty' :
                            kwargs["queryset"] = PneumaticSpringsQtyOption.objects.filter(
                                **filter_kwargs
                            )
                except PneumaticActuatorSelected.DoesNotExist :
                    pass

        return super().formfield_for_foreignkey(db_field , request , **kwargs)