from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.urls import path
from django.http import JsonResponse
from django.db.models import Prefetch
import json

from pneumatic_actuators.models.pa_actuator_selected import PneumaticActuatorSelected
from pneumatic_actuators.models.pa_options import (
    PneumaticSafetyPositionOption , PneumaticSpringsQtyOption ,
    PneumaticTemperatureOption , PneumaticIpOption ,
    PneumaticExdOption , PneumaticBodyCoatingOption
)



@admin.register(PneumaticActuatorSelected)
class PneumaticActuatorSelectedAdmin(admin.ModelAdmin) :
    list_display = [
        'name' , 'code' , 'selected_model_display' ,
        'safety_position_display' , 'springs_qty_display' ,
        'temperature_display' , 'ip_display' , 'exd_display' ,
        'body_coating_display' , 'sorting_order' , 'is_active'
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

    # Автодополнение (если нужно раскомментировать)
    # autocomplete_fields = ['selected_model', 'selected_safety_position', 'selected_springs_qty']

    fieldsets = (
        ('Основная информация' , {
            'fields' : (
                ('selected_model' , 'name' , 'code') ,'generate_description_btn'
            )
        }) ,
        ('Опции привода' , {
            'fields' : (
                ('selected_safety_position' , 'selected_springs_qty' , 'selected_temperature') ,
                ('selected_ip' , 'selected_exd' , 'selected_body_coating', 'selected_hand_wheel') ,
            ) ,
        }) ,
        # ('Сгенерированное описание' , {
        #     'fields' : ('description_preview' , 'generate_description_btn') ,
        #     'classes' : ('collapse' , 'wide') ,
        #     'description' : 'Описание будет сгенерировано автоматически на основе выбранных параметров'
        # }) ,
        ('Ручное описание (перезапишет сгенерированное)' , {
            'fields' : ('description' ,) ,
        })
    )

    # readonly_fields = ['description_preview' , 'generate_description_btn']
    readonly_fields = ['generate_description_btn']

    # Кастомная форма
    # class PneumaticActuatorSelectedForm(forms.ModelForm) :
    #     class Meta :
    #         model = PneumaticActuatorSelected
    #         fields = '__all__'
    #         widgets = {
    #             'description' : forms.Textarea(attrs={
    #                 'rows' : 60 ,
    #                 'cols' : 140 ,
    #                 'style' : 'width: 100%; font-family: "Consolas", monospace; '
    #                           'font-size: 13px; line-height: 1.4;' ,
    #                 'class' : 'full-description-textarea'
    #             }) ,
    #         }
    #
    #     def __init__(self , *args , **kwargs) :
    #         super().__init__(*args , **kwargs)
    #
    #         # Логика для DA моделей
    #         if self.instance and self.instance.selected_model :
    #             is_da = (self.instance.selected_model.pneumatic_actuator_variety and
    #                      self.instance.selected_model.pneumatic_actuator_variety.code == 'DA')
    #             if is_da :
    #                 self.fields['selected_safety_position'].required = False
    #
    # form = PneumaticActuatorSelectedForm

    class Media :
        js = ('admin/js/pneumatic_actuator_selected.js' ,)
        css = {
            'all' : ('admin/css/pneumatic_admin.css' ,)
        }

    def get_urls(self) :
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/generate-description/' ,
                self.admin_site.admin_view(self.generate_description_view) ,
                name='pneumatic_actuator_generate_description'
            ) ,
            path(
                'get_options/' ,
                self.admin_site.admin_view(self.get_options_view) ,
                name='pneumatic_actuator_get_options'
            ) ,
        ]
        return custom_urls + urls

    def generate_description_view(self , request , object_id) :
        """View для генерации описания"""
        try :
            instance = self.get_object(request , object_id)
            description = self._generate_description_for_instance(instance)

            # Обновляем описание в базе
            # instance.description = description
            # instance.save()

            return JsonResponse({
                'success' : True ,
                'description' : description ,
                'message' : 'Описание успешно сгенерировано'
            })
        except Exception as e :
            return JsonResponse({
                'success' : False ,
                'error' : str(e) ,
                'message' : 'Ошибка при генерации описания'
            } , status=500)

    def get_options_view(self , request) :
        """API для получения опций по модели"""
        model_id = request.GET.get('model_id')
        if not model_id :
            return JsonResponse({})

        # Здесь логика получения доступных опций для выбранной модели
        # Возвращаем JSON со списками доступных опций

        return JsonResponse({
            'safety_position' : [] ,
            'springs_qty' : [] ,
            'temperature' : [] ,
            'ip' : [] ,
            'exd' : [] ,
            'body_coating' : []
        })

    def _generate_description_for_instance(self , instance) :
        """Генерация описания для конкретного экземпляра"""
        # Используем ваш существующий метод
        return instance._generate_tech_description()

    def description_preview(self , obj) :
        """Поле для предпросмотра описания"""
        if not obj or not obj.pk :
            return "Сначала сохраните объект, чтобы сгенерировать описание"

        # Показываем либо сохраненное описание, либо генерацию на лету
        if obj.description :
            # Обрезаем для предпросмотра
            preview = obj.description
            # [:1500] + "..." if len(obj.description) > 1500 else obj.description
            return format_html(
                '<div class="description-preview">'
                '<h4>Текущее описание:</h4>'
                '<pre style="white-space: pre-wrap; background: #f5f5f5; padding: 10px; border-radius: 5px;">{}</pre>'
                '<p><small>Всего символов: {}</small></p>'
                '</div>' ,
                preview , len(obj.description)
            )
        else :
            return "Описание еще не сгенерировано. Нажмите кнопку ниже."

    description_preview.short_description = "Предпросмотр описания"

    def generate_description_btn(self, obj):
        """Кнопка для генерации описания"""
        if not obj or not obj.pk:
            return "Сначала сохраните объект"

        # Получаем CSRF токен
        request = None
        # Нужно получить request из контекста

        return format_html(
            '<button type="button" class="button generate-description-btn" '
            'data-object-id="{}">'  # Убрали data-csrf-token
            '🔄 Сгенерировать описание'
            '</button>'
            '<div class="description-status" style="margin-top: 10px;"></div>',
            obj.pk
        )

    generate_description_btn.short_description = "Действия"

    def get_queryset(self , request) :
        return super().get_queryset(request).select_related(
            'selected_model' ,
            'selected_safety_position__safety_position' ,
            'selected_springs_qty__springs_qty' ,
            'selected_temperature__model_line' ,
            'selected_ip__model_line' ,
            'selected_exd__model_line' ,
            'selected_body_coating__model_line'
        )

    # Методы для отображения в списке
    def selected_model_display(self , obj) :
        return obj.selected_model.name if obj.selected_model else "-"

    selected_model_display.short_description = "Модель"

    def safety_position_display(self , obj) :
        return obj.selected_safety_position.safety_position if obj.selected_safety_position else "-"

    safety_position_display.short_description = "Безопасное положение"

    def springs_qty_display(self , obj) :
        return obj.selected_springs_qty.springs_qty if obj.selected_springs_qty else "-"

    springs_qty_display.short_description = "Кол-во пружин"

    def temperature_display(self , obj) :
        return str(obj.selected_temperature) if obj.selected_temperature else "-"

    temperature_display.short_description = "Температура"

    def ip_display(self , obj) :
        return obj.selected_ip.ip_option if obj.selected_ip else "-"

    ip_display.short_description = "IP защита"

    def exd_display(self , obj) :
        return obj.selected_exd.exd_option if obj.selected_exd else "-"

    exd_display.short_description = "Взрывозащита"

    def body_coating_display(self , obj) :
        return obj.selected_body_coating.body_coating_option if obj.selected_body_coating else "-"

    body_coating_display.short_description = "Покрытие"