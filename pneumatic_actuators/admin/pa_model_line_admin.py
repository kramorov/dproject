# pneumatic_actuators/admin/pa_model_line_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from pneumatic_actuators.models.pa_model_line import PneumaticActuatorModelLine , PneumaticActuatorModelLineCertRelation
from pneumatic_actuators.models.pa_options import (
    PneumaticTemperatureOption ,
    PneumaticIpOption ,
    PneumaticExdOption ,
    PneumaticBodyCoatingOption
)

class CertDataInline(admin.TabularInline) :
    """Inline для температурных опций"""
    model = PneumaticActuatorModelLineCertRelation
    extra = 0
    ordering = ['sorting_order']
    fields = ['cert_data','is_active' , 'sorting_order']
    verbose_name = _("Сертификат")
    verbose_name_plural = _("Сертификаты")


class PneumaticTemperatureOptionInline(admin.TabularInline) :
    """Inline для температурных опций"""
    model = PneumaticTemperatureOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['encoding' , 'work_temp_min' , 'work_temp_max' , 'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Температурная опция")
    verbose_name_plural = _("Температурные опции")


class PneumaticIpOptionInline(admin.TabularInline) :
    """Inline для IP опций"""
    model = PneumaticIpOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['ip_option' , 'encoding' , 'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("IP опция")
    verbose_name_plural = _("IP опции")


class PneumaticExdOptionInline(admin.TabularInline) :
    """Inline для Exd опций"""
    model = PneumaticExdOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['exd_option' , 'encoding' , 'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Exd опция")
    verbose_name_plural = _("Exd опции")


class PneumaticBodyCoatingOptionInline(admin.TabularInline) :
    """Inline для опций покрытия корпуса"""
    model = PneumaticBodyCoatingOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['body_coating_option' , 'encoding' , 'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Опция покрытия")
    verbose_name_plural = _("Опции покрытия")


@admin.register(PneumaticActuatorModelLine)
class PneumaticActuatorModelLineAdmin(admin.ModelAdmin) :
    """Админка для серий пневмоприводов с through-опциями"""

    list_display = (
        'name' ,
        'code' ,
        'brand' ,
        'pneumatic_actuator_construction_variety' ,
        'ip_display' ,
        'exd_display' ,
        'sorting_order' ,
        'is_active'
    )

    list_editable = ('sorting_order' , 'is_active')
    list_filter = (
        'is_active' ,
        'brand' ,
        'pneumatic_actuator_construction_variety' ,
    )

    search_fields = (
        'name' ,
        'code' ,
        'description' ,
        'brand__name'
    )

    ordering = ('sorting_order' , 'name')

    # Поля для автодополнения
    # autocomplete_fields = [
    #     'brand' ,
    #     'default_output_type' ,
    #     'pneumatic_actuator_construction_variety' ,
    #     'default_hand_wheel'
    # ]

    # Inline для всех типов опций
    inlines = [
        PneumaticTemperatureOptionInline ,
        PneumaticIpOptionInline ,
        PneumaticExdOptionInline ,
        PneumaticBodyCoatingOptionInline,
        CertDataInline
    ]

    fieldsets = (
        (_('Основная информация') , {
            'fields' : (
                ('name' , 'code' , 'brand' ,
                'pneumatic_actuator_construction_variety'), 'model_item_code_template', 'description'
            )
        }) ,
        (_('Основные параметры') , {
            'fields' : ('default_output_type' ,)
        }) ,
        (_('Ручной дублер') , {
            'fields' : ('default_hand_wheel' ,)
        }) ,
        (_('Настройки') , {
            'fields' : ('sorting_order' , 'is_active')
        }) ,
    )

    def get_queryset(self , request) :
        """Оптимизация запросов с учетом through-моделей"""
        return super().get_queryset(request).select_related(
            'brand' ,
            'default_output_type' ,
            'pneumatic_actuator_construction_variety' ,
            'default_hand_wheel'
        ).prefetch_related(
            'temperature_options' ,
            'ip_options' ,
            'exd_options' ,
            'body_coating_options' ,
            'ip_options__ip_option' ,
            'exd_options__exd_option' ,
            'body_coating_options__body_coating_option'
        )

    def temperature_range_display(self , obj) :
        """Отображение температурного диапазона в списке"""
        return obj.temperature_range_display

    temperature_range_display.short_description = _('Температура')

    def ip_display(self , obj) :
        """Отображение IP защиты в списке"""
        return obj.ip_display

    ip_display.short_description = _('IP защита')

    def exd_display(self , obj) :
        """Отображение взрывозащиты в списке"""
        return obj.exd_display

    exd_display.short_description = _('Взрывозащита')

    def body_coating_display(self , obj) :
        """Отображение покрытия корпуса в списке"""
        return obj.body_coating_display

    body_coating_display.short_description = _('Покрытие')

    def save_model(self , request , obj , form , change) :
        """Сохранение модели с созданием опций по умолчанию"""
        super().save_model(request , obj , form , change)

        # Если это новая модель, создаем опции по умолчанию
        if not change :
            obj.ensure_all_default_options_exist()

    def save_formset(self , request , form , formset , change) :
        """Упрощенное сохранение с проверкой после записи"""
        if formset.model in [PneumaticTemperatureOption , PneumaticIpOption ,
                             PneumaticExdOption , PneumaticBodyCoatingOption] :

            # 1. Сначала сохраняем все объекты
            instances = formset.save(commit=False)
            for instance in instances :
                instance.save()

            for instance in formset.deleted_objects :
                instance.delete()

            # 2. Проверяем после сохранения
            parent_obj = form.instance
            self._check_default_options_after_save(request , formset.model , parent_obj)

        else :
            super().save_formset(request , form , formset , change)

    def _check_default_options_after_save(self , request , option_model , parent_obj) :
        """Проверка стандартных опций после сохранения"""
        parent_field = option_model._get_parent_field_name()
        if not parent_field :
            return

        # Ищем все стандартные опции
        default_options = option_model.objects.filter(
            **{parent_field : parent_obj , 'is_default' : True , 'is_active' : True}
        )

        # Если больше одной - показываем сообщение
        if default_options.count() > 1 :
            from django.contrib import messages
            option_name = option_model._meta.verbose_name.lower()
            messages.warning(
                request ,
                f'Обнаружено несколько стандартных опций {option_name}. '
                f'Пожалуйста, оставьте только одну стандартную опцию.'
            )