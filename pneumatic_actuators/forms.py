# pneumatic_actuators/forms.py

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import PneumaticActuatorSelected
from .models.pa_options import PneumaticSafetyPositionOption , PneumaticSpringsQtyOption , PneumaticTemperatureOption , \
    PneumaticIpOption , PneumaticExdOption , PneumaticBodyCoatingOption , PneumaticHandWheelOption


class PneumaticActuatorSelectedForm(forms.ModelForm) :
    """Форма для редактирования выбранного привода"""

    class Meta :
        model = PneumaticActuatorSelected
        fields = [
            'name' , 'code' , 'description' ,
            'selected_model_line_item' ,
            'selected_safety_position' ,
            'selected_springs_qty' ,
            'selected_temperature' ,
            'selected_ip' ,
            'selected_exd' ,
            'selected_body_coating' ,
            'selected_hand_wheel' ,
            'sorting_order' , 'is_active'
        ]
        widgets = {
            'name' : forms.TextInput(attrs={
                'class' : 'form-control' ,
                'size' : 80 ,
                'style' : 'width: 80%'
            }) ,
            'code' : forms.TextInput(attrs={
                'class' : 'form-control' ,
                'size' : 30 ,
                'style' : 'width: 50%'
            }) ,
            'description' : forms.Textarea(attrs={
                'class' : 'form-control' ,
                'rows' : 4 ,
                'cols' : 80 ,
                'style' : 'width: 90%'
            }) ,
            'selected_model_line_item' : forms.Select(attrs={'class' : 'form-control'}) ,
            'selected_safety_position' : forms.Select(attrs={'class' : 'form-control'}) ,
            'selected_springs_qty' : forms.Select(attrs={'class' : 'form-control'}) ,
            'selected_temperature' : forms.Select(attrs={'class' : 'form-control'}) ,
            'selected_ip' : forms.Select(attrs={'class' : 'form-control'}) ,
            'selected_exd' : forms.Select(attrs={'class' : 'form-control'}) ,
            'selected_body_coating' : forms.Select(attrs={'class' : 'form-control'}) ,
            'selected_hand_wheel' : forms.Select(attrs={'class' : 'form-control'}) ,
            'sorting_order' : forms.NumberInput(attrs={'class' : 'form-control' , 'style' : 'width: 100px'}) ,
            'is_active' : forms.CheckboxInput(attrs={'class' : 'form-check-input'}) ,
        }

    def __init__(self , *args , **kwargs) :
        super().__init__(*args , **kwargs)

        # Динамически ограничиваем выбор опций в зависимости от выбранной модели
        instance = kwargs.get('instance')
        selected_model = instance.selected_model_line_item if instance else None

        if selected_model :
            # Ограничиваем опции только доступными для выбранной модели
            self._limit_option_choices(selected_model)

    def _limit_option_choices(self , selected_model) :
        """Ограничить выбор опций в зависимости от модели"""
        # Опции через model_line_item
        if selected_model :
            self.fields['selected_safety_position'].queryset = \
                PneumaticSafetyPositionOption.objects.filter(
                    model_line_item=selected_model ,
                    is_active=True
                )
            self.fields['selected_springs_qty'].queryset = \
                PneumaticSpringsQtyOption.objects.filter(
                    model_line_item=selected_model ,
                    is_active=True
                )

            # Опции через model_line
            if selected_model.model_line :
                model_line = selected_model.model_line
                self.fields['selected_temperature'].queryset = \
                    PneumaticTemperatureOption.objects.filter(
                        model_line=model_line ,
                        is_active=True
                    )
                self.fields['selected_ip'].queryset = \
                    PneumaticIpOption.objects.filter(
                        model_line=model_line ,
                        is_active=True
                    )
                self.fields['selected_exd'].queryset = \
                    PneumaticExdOption.objects.filter(
                        model_line=model_line ,
                        is_active=True
                    )
                self.fields['selected_body_coating'].queryset = \
                    PneumaticBodyCoatingOption.objects.filter(
                        model_line=model_line ,
                        is_active=True
                    )
                self.fields['selected_hand_wheel'].queryset = \
                    PneumaticHandWheelOption.objects.filter(
                        model_line=model_line ,
                        is_active=True
                    )

    def clean(self) :
        cleaned_data = super().clean()
        selected_model = cleaned_data.get('selected_model_line_item')

        if not selected_model :
            return cleaned_data

        # Валидация опций
        option_fields = [
            'selected_safety_position' , 'selected_springs_qty' ,
            'selected_temperature' , 'selected_ip' , 'selected_exd' ,
            'selected_body_coating' , 'selected_hand_wheel'
        ]

        for field_name in option_fields :
            value = cleaned_data.get(field_name)
            if value :
                # Проверяем, что опция доступна для выбранной модели
                if not self._is_option_available(selected_model , field_name , value) :
                    self.add_error(field_name , _('Эта опция не доступна для выбранной модели'))
                    cleaned_data[field_name] = None

        return cleaned_data

    def _is_option_available(self , selected_model , field_name , value) :
        """Проверить, доступна ли опция для выбранной модели"""
        try :
            if field_name in ['selected_safety_position' , 'selected_springs_qty'] :
                return value.model_line_item == selected_model
            else :
                if selected_model.model_line :
                    return value.model_line == selected_model.model_line
                return False
        except AttributeError :
            return False