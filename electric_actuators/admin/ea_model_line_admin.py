#electric_actuators/admin/ea_model_line_admin.py

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from electric_actuators.models import ModelLine, ElectricTemperatureOption, ElectricIpOption, ElectricHandWheelOption, \
    ElectricExdOption, ElectricBodyCoatingOption, ElectricActuatorModelLine, ElectricTurnAngleOption, \
    ElectricBlinkerOption, ElectricPowerSupplyOption, ElectricWaySwitchesOption, ElectricControlUnitInstalledOption


def copy_electric_actuator_data(modeladmin, request, queryset):
    for obj in queryset:
        # Копируем объект
        obj.pk = None  # Убираем primary key, чтобы создать новый объект
        obj.name = obj.name + '(Копия)'
        obj.save()


copy_electric_actuator_data.short_description = "Копировать выбранные записи"


@admin.register(ModelLine)
class ModelLineAdmin(admin.ModelAdmin):
    ordering = ['name']
    # Показать важные поля в списке объектов модели
    list_display = ('name', 'default_output_type', 'brand')

    fieldsets = (
        ('Общая информация', {
            'fields': (
                ('name', 'default_output_type', 'brand',), 'default_blinker')
        }),
        ('Опции', {
            'fields': (
                ('default_ip', 'allowed_ip'), ('default_exd', 'allowed_exd'),
                ('default_body_coating', 'allowed_body_coating'),
                ('default_temperature', 'allowed_temperature'),
                ('default_control_unit_installed', 'allowed_control_unit_installed'),)
        }),
        ('Конечные, путевые выключатели и датчики момента', {
            'fields': (
                ('default_end_switches', 'allowed_end_switches'), ('default_way_switches', 'allowed_way_switches'),
                ('default_torque_switches', 'allowed_torque_switches'))
        }),
        ('Прочее', {
            'fields': (
                ('default_hand_wheel', 'allowed_hand_wheel'), ('default_operating_mode', 'allowed_operating_mode'),
                )
        }),
    )

    actions = [copy_electric_actuator_data]  # Добавляем действие для копирования

class ElectricControlUnitInstalledOptionInline(admin.TabularInline) :
    """Inline для напряжения питания"""
    model = ElectricControlUnitInstalledOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['encoding' ,  'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Блок управления")
    verbose_name_plural = _("Опции блоков управления")

class ElectricWaySwitchesOptionInline(admin.TabularInline) :
    """Inline для напряжения питания"""
    model = ElectricWaySwitchesOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['encoding' ,  'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Путевые выключатели")
    verbose_name_plural = _("Опции путевых выключателей")


class ElectricPowerSupplyOptionInline(admin.TabularInline) :
    """Inline для напряжения питания"""
    model = ElectricPowerSupplyOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['encoding' ,  'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Напряжение")
    verbose_name_plural = _("Опции напряжения питания")


class ElectricBlinkerOptionInline(admin.TabularInline) :
    """Inline для температурных опций"""
    model = ElectricBlinkerOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['encoding' ,  'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Блинкер")
    verbose_name_plural = _("Опции блинкера")

class ElectricTurnAngleOptionInline(admin.TabularInline) :
    """Inline для опций угла поворота"""
    model = ElectricTurnAngleOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['encoding' ,  'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Угол поворота")
    verbose_name_plural = _("Опции угла поворота")


class ElectricTemperatureOptionInline(admin.TabularInline) :
    """Inline для температурных опций"""
    model = ElectricTemperatureOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['encoding' , 'work_temp_min' , 'work_temp_max' , 'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Температурная опция")
    verbose_name_plural = _("Температурные опции")


class ElectricIpOptionInline(admin.TabularInline) :
    """Inline для IP опций"""
    model = ElectricIpOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['ip_option' , 'encoding' , 'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("IP опция")
    verbose_name_plural = _("IP опции")

class ElectricHandWheelOptionInline(admin.TabularInline) :
    """Inline для PneumaticHandWheelOption опций"""
    model = ElectricHandWheelOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['hand_wheel_option' , 'encoding' , 'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Опция ручного дублера")
    verbose_name_plural = _("Опции ручного дублера")

class ElectricExdOptionInline(admin.TabularInline) :
    """Inline для Exd опций"""
    model = ElectricExdOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['exd_option' , 'encoding' , 'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Exd опция")
    verbose_name_plural = _("Exd опции")


class ElectricBodyCoatingOptionInline(admin.TabularInline) :
    """Inline для опций покрытия корпуса"""
    model = ElectricBodyCoatingOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['body_coating_option' , 'encoding' , 'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Опция покрытия")
    verbose_name_plural = _("Опции покрытия")


@admin.register(ElectricActuatorModelLine)
class ElectricActuatorModelLineAdmin(admin.ModelAdmin) :
    """Админка для серий пневмоприводов с through-опциями"""

    list_display = (
        'name' ,
        'code' ,
        'brand' ,
        'ip_display' ,
        'exd_display' ,
        'default_output_type',
        'sorting_order' ,
        'is_active'
    )

    list_editable = ('sorting_order' , 'is_active')
    list_filter = (
        'is_active' ,
        'brand' ,
        'default_output_type' ,
    )

    search_fields = (
        'name' ,
        'code' ,
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
    inlines = [ElectricPowerSupplyOptionInline, ElectricTurnAngleOptionInline,
        ElectricTemperatureOptionInline ,
        ElectricIpOptionInline ,
        ElectricExdOptionInline ,
        ElectricHandWheelOptionInline,
        ElectricBodyCoatingOptionInline,
        ElectricWaySwitchesOptionInline, ElectricBlinkerOptionInline
    ]

    fieldsets = (
        (_('Основная информация') , {
            'fields' : (
                ('name' , 'code' , 'brand' ,
                'default_output_type'), 'model_item_code_template', 'description'
            )
        }) ,
        (_('Основные параметры') , {
            'fields' : ('default_output_type' ,)
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
        ).prefetch_related(
            'temperature_options' ,
            'ip_options' ,
            'exd_options' ,
            'body_coating_options' ,
            'hand_wheel_options',
            'ip_options' ,
            'exd_options' ,
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
        if formset.model in [ElectricTurnAngleOption , ElectricHandWheelOption ,ElectricTemperatureOption,
                             ElectricBlinkerOption , ElectricPowerSupplyOption, ElectricIpOption,
                             ElectricExdOption, ElectricWaySwitchesOption, ElectricBodyCoatingOption,
                             ElectricControlUnitInstalledOption] :

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