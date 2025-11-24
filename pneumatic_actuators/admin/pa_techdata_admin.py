from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django import forms

from pneumatic_actuators.models import PneumaticActuatorTechDataTableDrawingItem
from pneumatic_actuators.models.pa_techdata import PneumaticActuatorTechDataTable


class PneumaticActuatorTechDataTableForm(forms.ModelForm) :
    """Форма для таблицы технических данных пневмоприводов"""

    class Meta :
        model = PneumaticActuatorTechDataTable
        fields = '__all__'
        widgets = {
            'description' : forms.Textarea(attrs={'rows' : 3}) ,
            'code' : forms.TextInput(attrs={'style' : 'width: 200px;'}) ,
        }


class PneumaticActuatorTechDataTableDrawingItemInline(admin.TabularInline) :
    """
    Inline для связи таблицы техданных с чертежами
    """
    model = PneumaticActuatorTechDataTableDrawingItem  # ← ИСПОЛЬЗУЙТЕ КЛАСС МОДЕЛИ, НЕ СТРОКУ
    extra = 1
    verbose_name = _('Чертеж')
    verbose_name_plural = _('Чертежи')

    # Поля для отображения в inline
    fields = ('drawing' , 'sorting_order' , 'is_active')
    # ordering = ('sorting_order' ,)

    # Автодополнение для поля drawing
    autocomplete_fields = ['drawing']


@admin.register(PneumaticActuatorTechDataTable)
class PneumaticActuatorTechDataTableAdmin(admin.ModelAdmin) :
    """Админка для таблиц технических данных пневмоприводов"""

    form = PneumaticActuatorTechDataTableForm
    list_display = (
        'name' , 'code' , 'drawings_count' , 'description_preview'
    )
    list_filter = ()
    search_fields = ('name' , 'code' , 'description')
    ordering = ('name' , 'code')

    # Поля для автодополнения в форме
    autocomplete_fields = []

    # Inline для отображения связанных чертежей
    inlines = [PneumaticActuatorTechDataTableDrawingItemInline]

    fieldsets = (
        (_('Основная информация') , {
            'fields' : (
                'name' , 'code' , 'description'
            )
        }) ,
    )

    def get_queryset(self , request) :
        """Оптимизация запросов к базе данных"""
        return super().get_queryset(request).prefetch_related('drawings')

    def drawings_count(self , obj) :
        """Количество связанных чертежей"""
        return obj.drawings.count()

    drawings_count.short_description = _('Чертежи')
    drawings_count.admin_order_field = 'drawings__count'

    def description_preview(self , obj) :
        """Превью описания"""
        if obj.description :
            return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
        return '-'

    description_preview.short_description = _('Описание')

    def get_readonly_fields(self , request , obj=None) :
        """Поля только для чтения"""
        if obj :  # При редактировании существующего объекта
            return ['code']
        return []

    def save_model(self , request , obj , form , change) :
        """Дополнительная логика при сохранении"""
        if not change :  # Только при создании
            # Можно добавить автоматическую генерацию кода, если нужно
            pass
        super().save_model(request , obj , form , change)

    class Media :
        css = {
            'all' : ('admin/css/pneumatic_techdata.css' ,)
        }