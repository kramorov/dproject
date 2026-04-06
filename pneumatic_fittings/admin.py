# pneumatic_fittings/admin.py
from django.contrib import admin
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import PneumaticFittingVariety , PneumaticFitting , PneumaticFittingModelLine


@admin.register(PneumaticFittingVariety)
class PneumaticFittingVarietyAdmin(admin.ModelAdmin) :
    list_display = ['name' , 'code' , 'sorting_order' , 'is_active']
    list_editable = ['sorting_order' , 'is_active']
    list_filter = ['is_active']
    search_fields = ['name' , 'code' , 'description']
    fieldsets = (
        (_('Основная информация') , {
            'fields' : ('name' , 'code' , 'description')
        }) ,
        (_('Настройки отображения') , {
            'fields' : ('sorting_order' , 'is_active')
        }) ,
    )


class PneumaticFittingForm(forms.ModelForm) :
    class Meta :
        model = PneumaticFitting
        fields = '__all__'
        widgets = {
            'name' : forms.TextInput(
                attrs={'size' : 80 , 'style' : 'width: 80%' , 'placeholder' : 'Введите название фитинга'}) ,
            'code' : forms.TextInput(attrs={'size' : 30 , 'style' : 'width: 50%'}) ,
            'description' : forms.Textarea(attrs={'rows' : 6 , 'cols' : 80 , 'style' : 'width: 90%'}) ,
        }


@admin.register(PneumaticFitting)
class PneumaticFittingAdmin(admin.ModelAdmin) :
    form = PneumaticFittingForm
    list_display = [
        'name' , 'code' , 'brand' , 'fitting_model_line', 'fitting_variety' ,
        'pipe_diameter' , 'thread' , 'thread_inner_outer' , 'sorting_order' , 'is_active'
    ]
    list_editable = ['code' , 'brand' , 'fitting_model_line','sorting_order' , 'is_active']
    list_filter = [
        'brand' , 'fitting_model_line__code','fitting_variety' ,
        'body_material' , 'pipe_material' , 'pipe_diameter' , 'thread' , 'thread_inner_outer'
    ]
    search_fields = ['name' , 'code' , 'description']

    # autocomplete_fields = ['producer', 'brand', 'fitting_variety', 'body_material', 'pipe_material', 'thread']

    fieldsets = (
        (_('Основная информация') , {
            'fields' : ('name' , ('code' , 'fitting_variety' , 'fitting_model_line',) ,
                        ('producer' , 'brand' , 'body_material' ,) ,
                        ('pipe_material' , 'pipe_diameter') , ('thread' , 'thread_inner_outer') ,
                        ('description' , 'sorting_order' , 'is_active'))
        }) ,
        (_('Для глушителей') , {
            'fields' : (('flow_rate','noise_level' , 'operating_pressure' )) ,
        }) ,
    )

    def get_queryset(self , request) :
        return super().get_queryset(request).select_related(
            'producer' , 'brand' , 'fitting_variety' ,
            'body_material' , 'pipe_material' , 'thread'
        )

    actions = ['copy_selected_fittings']

    def copy_selected_fittings(self , request , queryset) :
        """Action для копирования выбранных фитингов"""
        copied_count = 0
        for fitting in queryset :
            # Создаем копию без сохранения, чтобы пользователь мог изменить
            copy_obj = fitting.copy(save_copy=False)
            # copy_obj.name = f"Копия {fitting.name}"

            # Сохраняем копию
            copy_obj.save()
            copied_count += 1

        self.message_user(
            request ,
            f'Успешно скопировано {copied_count} фитинг(ов)'
        )

    copy_selected_fittings.short_description = "Копировать выбранные фитинги"


class PneumaticFittingModelLineForm(forms.ModelForm) :
    class Meta :
        model = PneumaticFitting
        fields = '__all__'
        widgets = {
            'name' : forms.TextInput(attrs={
                'size' : 80 ,
                'style' : 'width: 80%' ,
                'placeholder' : 'Введите текст названия фитинга'
            }) ,
            'name_template' : forms.Textarea(attrs={
                'rows' : 3 ,  # количество строк
                'cols' : 80 ,
                'style' : 'width: 90%; height: 80px;' ,  # можно задать высоту
                'placeholder' : 'Введите шаблон для текстового названия фитинга'
            }) ,
            'description_template' : forms.Textarea(attrs={
                'rows' : 3 ,  # количество строк
                'cols' : 80 ,
                'style' : 'width: 90%; height: 80px;' ,  # можно задать высоту
                'placeholder' : 'Введите шаблон для описания фитинга'
            }) ,
            'description' : forms.Textarea(attrs={
                'rows' : 3 ,
                'cols' : 80 ,
                'style' : 'width: 90%' ,
                'placeholder' : 'Введите описание'
            }) ,
        }


@admin.register(PneumaticFittingModelLine)
class PneumaticFittingModelLineAdmin(admin.ModelAdmin) :
    form = PneumaticFittingModelLineForm
    list_display = [
        'name' , 'code' , 'brand' , 'fitting_variety' ,
        'pipe_material' , 'body_material' , 'sorting_order' , 'is_active'
    ]
    list_editable = ['sorting_order' , 'is_active']
    list_filter = [
        'brand' , 'fitting_variety' ,
        'body_material' , 'pipe_material' ,
    ]

    fieldsets = (
        (_('Основная информация') , {
            'fields' : ('name' , ('code' , 'fitting_variety' ,) ,
                        ('producer' , 'brand' ,) ,
                        ('pipe_material' , 'body_material' ,) ,
                        ('work_temp_min' , 'work_temp_max') ,
                        ('pressure_min' , 'pressure_max') ,
                        'name_template' ,
                        'description_template' ,
                        'description' , ('sorting_order' , 'is_active'))
        }) ,
    )

    def get_queryset(self , request) :
        return super().get_queryset(request).select_related(
            'producer' , 'brand' , 'fitting_variety' ,
            'body_material' , 'pipe_material'
        )

    actions = ['copy_selected_fitting_model_line']

    def copy_selected_fitting_model_line(self , request , queryset) :
        """Action для копирования выбранных фитингов"""
        copied_count = 0
        for fitting in queryset :
            # Создаем копию без сохранения, чтобы пользователь мог изменить
            copy_obj = fitting.copy(save_copy=False)
            # copy_obj.name = f"Копия {fitting.name}"

            # Сохраняем копию
            copy_obj.save()
            copied_count += 1

        self.message_user(
            request ,
            f'Успешно скопировано {copied_count} фитинг(ов)'
        )

    copy_selected_fitting_model_line.short_description = "Копировать выбранные фитинги"
