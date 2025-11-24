from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django import forms
from pneumatic_actuators.models.pa_techdata_drawing_item import PneumaticActuatorTechDataTableDrawingItem


class PneumaticActuatorTechDataTableDrawingItemForm(forms.ModelForm) :
    """Форма для связи таблицы техданных с чертежами"""

    class Meta :
        model = PneumaticActuatorTechDataTableDrawingItem
        fields = '__all__'
        widgets = {
            'description' : forms.Textarea(attrs={'rows' : 3}) ,
            'display_order' : forms.NumberInput(attrs={'style' : 'width: 100px;'}) ,
        }


class AllowedBodyFilter(admin.SimpleListFilter) :
    """Фильтр по наличию привязанных корпусов"""
    title = _('Наличие корпусов')
    parameter_name = 'has_allowed_body'

    def lookups(self , request , model_admin) :
        return (
            ('yes' , _('Есть корпуса')) ,
            ('no' , _('Нет корпусов')) ,
        )

    def queryset(self , request , queryset) :
        if self.value() == 'yes' :
            return queryset.filter(allowed_body__isnull=False).distinct()
        if self.value() == 'no' :
            return queryset.filter(allowed_body__isnull=True)
        return queryset


@admin.register(PneumaticActuatorTechDataTableDrawingItem)
class PneumaticActuatorTechDataTableDrawingItemAdmin(admin.ModelAdmin) :
    """Админка для связи таблиц технических данных с чертежами"""

    form = PneumaticActuatorTechDataTableDrawingItemForm
    list_display = (
        'tech_data_table' , 'drawing' , 'allowed_body_count' ,
        'display_order' , 'description_preview'
    )
    list_editable = ('display_order' ,)
    list_filter = (
        'tech_data_table' ,
        AllowedBodyFilter ,
    )
    search_fields = (
        'tech_data_table__name' ,
        'tech_data_table__code' ,
        'drawing__title' ,
        'drawing__description' ,
        'description'
    )
    ordering = ('tech_data_table__name' , 'display_order' , 'drawing__title')

    # Поля для автодополнения в форме
    autocomplete_fields = ['tech_data_table' , 'drawing']

    # Фильтры для ManyToMany полей
    filter_horizontal = ('allowed_body' ,)

    fieldsets = (
        (_('Основная связь') , {
            'fields' : (
                'tech_data_table' , 'drawing' , 'display_order'
            )
        }) ,
        (_('Применимые корпуса') , {
            'fields' : ('allowed_body' ,) ,
            'description' : _('Выберите корпуса моделей, для которых применим этот чертеж')
        }) ,
        (_('Дополнительная информация') , {
            'fields' : ('description' ,) ,
            'classes' : ('collapse' ,)  # Сворачиваемый блок
        }) ,
    )

    def get_queryset(self , request) :
        """Оптимизация запросов к базе данных"""
        return super().get_queryset(request).select_related(
            'tech_data_table' , 'drawing'
        ).prefetch_related('allowed_body')

    def allowed_body_count(self , obj) :
        """Количество привязанных корпусов"""
        return obj.allowed_body.count()

    allowed_body_count.short_description = _('Корпуса')
    allowed_body_count.admin_order_field = 'allowed_body__count'

    def description_preview(self , obj) :
        """Превью описания"""
        if obj.description :
            return obj.description[:80] + '...' if len(obj.description) > 80 else obj.description
        return '-'

    description_preview.short_description = _('Описание')

    def get_readonly_fields(self , request , obj=None) :
        """Поля только для чтения"""
        # Можно сделать некоторые поля readonly при необходимости
        return []

    def save_model(self , request , obj , form , change) :
        """Дополнительная логика при сохранении"""
        # Автоматически устанавливаем порядок отображения, если не задан
        if not obj.display_order and not change :
            last_item = PneumaticActuatorTechDataTableDrawingItem.objects.filter(
                tech_data_table=obj.tech_data_table
            ).order_by('-display_order').first()
            obj.display_order = (last_item.display_order + 1) if last_item else 0

        super().save_model(request , obj , form , change)

    def formfield_for_manytomany(self , db_field , request , **kwargs) :
        """Кастомизация поля ManyToMany"""
        if db_field.name == "allowed_body" :
            # Ограничиваем queryset для allowed_body
            kwargs["queryset"] = db_field.related_model.objects.filter(is_active=True)
        return super().formfield_for_manytomany(db_field , request , **kwargs)

    class Media :
        css = {
            'all' : ('admin/css/pneumatic_techdata_drawing.css' ,)
        }
        js = ('admin/js/pneumatic_techdata_drawing.js' ,)  # Если нужны кастомные скрипты