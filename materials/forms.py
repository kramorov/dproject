# materials/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import MaterialSpecified


class MaterialSpecifiedAddForm(forms.ModelForm) :
    """Форма для добавления нового материала"""

    class Meta :
        model = MaterialSpecified
        fields = [
            'material_general' , 'material_detailed' ,
            'description' ,
            'work_temp_min' , 'work_temp_max' ,
            'temp_min' , 'temp_max'
        ]
        widgets = {
            'description' : forms.Textarea(attrs={'rows' : 10 , 'cols' : 80}) ,
        }


class MaterialSpecifiedChangeForm(forms.ModelForm) :
    """Форма для редактирования существующего материала"""

    class Meta :
        model = MaterialSpecified
        fields = [
            'material_general' , 'material_detailed' , 'name' ,
            'description' ,
            'work_temp_min' , 'work_temp_max' , 'temp_min' , 'temp_max'
        ]
        widgets = {
            'name' : forms.TextInput(attrs={ 'size' : 100}) ,
            'description' : forms.Textarea(attrs={'rows' : 10 , 'cols' : 80}) ,
        }