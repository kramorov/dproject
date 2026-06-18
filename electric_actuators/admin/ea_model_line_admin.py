#electric_actuators/admin/ea_model_line_admin.py
from django.db import models
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from electric_actuators.models import ElectricTemperatureOption , ElectricIpOption , \
    ElectricHandWheelOption , \
    ElectricExdOption , ElectricBodyCoatingOption , ElectricActuatorModelLine , ElectricTurnAngleOption , \
    ElectricBlinkerOption , ElectricWaySwitchesOption , ElectricControlUnitInstalledOption , \
    ElectricMechanicalIndicatorOption , ElectricOperatingModeOption , ModelLine , ElectricBodyColorOption
import logging
from electric_actuators.models.ea_allowed_options import (
    AllowedControlUnitOption ,
    AllowedTurnCounterOption ,
    AllowedSignalProfileOption ,
)
from django.shortcuts import redirect
from django.contrib import messages
from django.db import transaction
import uuid

logger = logging.getLogger(__name__)


def copy_electric_actuator_model_line(modeladmin, request, queryset):
    """Копировать выбранные записи с сохранением связанных данных"""
    if not request.user.has_perm('electric_actuators.add_electricactuatormodelline'):
        messages.error(request, _('У вас нет прав на добавление новых записей.'))
        return

    success_count = 0
    error_count = 0

    for original_obj in queryset:
        try:
            with transaction.atomic():
                # Создаем копию основного объекта
                # ВАЖНО: Создаем новый экземпляр, а не переиспользуем старый
                new_obj = original_obj.__class__()

                # Копируем все поля кроме id и ManyToMany
                for field in original_obj._meta.fields:
                    if field.name not in ['id', 'pk'] and not field.many_to_many:
                        value = getattr(original_obj, field.name)
                        setattr(new_obj, field.name, value)

                # Добавляем "(Копия)" к имени и коду
                if new_obj.name:
                    new_obj.name = f"{new_obj.name} (Копия)"

                if new_obj.code:
                    new_obj.code = f"{new_obj.code} (Копия)"

                # Сохраняем новый объект
                new_obj.save()

                # Копируем ManyToMany поля
                # allowed_operating_mode
                if hasattr(original_obj, 'allowed_operating_mode'):
                    new_obj.allowed_operating_mode.set(original_obj.allowed_operating_mode.all())

                # Копируем Inline опции
                copy_related_options(original_obj, new_obj)

                success_count += 1
                messages.success(request, f"Скопировано: {original_obj.name} -> {new_obj.name}")
                logger.info(f"Скопирована серия: {original_obj.name} -> {new_obj.name}")

        except Exception as e:
            error_count += 1
            logger.error(f"Ошибка копирования {original_obj}: {e}", exc_info=True)
            messages.error(request, f"Ошибка при копировании {original_obj}: {str(e)[:100]}")

    # Сообщения пользователю
    if success_count > 0:
        messages.success(request, f"Успешно скопировано {success_count} записей.")
    if error_count > 0:
        messages.warning(request, f"Не удалось скопировать {error_count} записей.")


copy_electric_actuator_model_line.short_description = _("Копировать выбранные записи")


def copy_related_options(original_obj, new_obj):
    """Копировать все связанные опции"""
    # Список всех типов опций для копирования
    option_configs = [
        ('temperature_options', 'encoding'),
        ('ip_options', 'encoding'),
        ('exd_options', 'encoding'),
        ('body_coating_options', 'encoding'),
        ('blinker_options', 'encoding'),
        # ('end_switches_options', 'encoding'),
        # ('way_switches_options', 'encoding'),
        # ('torque_switches_options', 'encoding'),
        ('control_unit_options', 'encoding'),
        ('hand_wheel_options', 'encoding'),
        ('mechanical_indicator_options', 'encoding'),
        ('allowed_control_units', 'encoding'),
        ('allowed_turn_counters', 'encoding'),
        ('allowed_signal_profiles', 'encoding'),
        ('operating_mode_options', 'encoding'),
        ('turn_angle_options', 'encoding'),
    ]

    for related_name, encoding_field in option_configs:
        if hasattr(original_obj, related_name):
            try:
                copy_options(original_obj, new_obj, related_name, encoding_field)
                logger.debug(f"Скопированы опции: {related_name}")
            except Exception as e:
                logger.warning(f"Ошибка копирования {related_name}: {e}")


def copy_options(original_obj, new_obj, related_name, encoding_field='encoding'):
    """Копировать конкретный тип опций"""
    related_manager = getattr(original_obj, related_name)

    for original_option in related_manager.all():
        # Создаем новую опцию того же класса
        new_option = original_option.__class__()

        # Копируем все поля кроме id и связи с родителем
        for field in original_option._meta.fields:
            field_name = field.name

            # Пропускаем id и поле связи с родительским объектом
            if field_name in ['id', 'pk']:
                continue

            # Если это ForeignKey, но не ссылается на родительский объект
            if isinstance(field, models.ForeignKey):
                # Проверяем, ссылается ли поле на родительский класс
                if field.related_model == original_obj.__class__:
                    # Это поле связи с родителем - устанавливаем новый объект
                    setattr(new_option, field_name, new_obj)
                else:
                    # Это другая ForeignKey - копируем значение
                    value = getattr(original_option, field_name)
                    setattr(new_option, field_name, value)
            else:
                # Обычное поле - копируем значение
                value = getattr(original_option, field_name)
                setattr(new_option, field_name, value)

        # Генерируем новую кодировку, чтобы избежать дублирования
        if hasattr(new_option, encoding_field) and getattr(new_option, encoding_field):
            current_encoding = getattr(new_option, encoding_field)
            # Добавляем суффикс к кодировке
            if current_encoding:
                # Генерируем уникальный суффикс
                suffix = str(uuid.uuid4())[:8]  # первые 8 символов UUID
                setattr(new_option, encoding_field, f"{current_encoding}_COPY_{suffix}")

        # Сохраняем новую опцию
        try:
            new_option.full_clean()  # Валидация
            new_option.save()

            # Если у опции есть свои ManyToMany поля, копируем их
            copy_option_m2m(original_option, new_option)

        except Exception as e:
            logger.warning(f"Ошибка сохранения опции {related_name}: {e}")
            # Попробуем без уникальной кодировки
            if hasattr(new_option, encoding_field):
                setattr(new_option, encoding_field, f"COPY_{uuid.uuid4().hex[:8]}")
                try:
                    new_option.save()
                except Exception as e2:
                    logger.error(f"Не удалось сохранить опцию даже с новой кодировкой: {e2}")


def copy_option_m2m(original_option, new_option):
    """Копировать ManyToMany связи опции"""
    for field in original_option._meta.many_to_many:
        field_name = field.name
        if hasattr(original_option, field_name):
            try:
                getattr(new_option, field_name).set(
                    getattr(original_option, field_name).all()
                )
            except Exception as e:
                logger.debug(f"Не удалось скопировать M2M {field_name}: {e}")


def get_parent_field_name(option_instance, parent_class):
    """Получить имя поля связи с родительским объектом"""
    for field in option_instance._meta.fields:
        if isinstance(field, models.ForeignKey):
            if field.related_model == parent_class:
                return field.name
    return None

#
# @admin.register(ModelLine)
# class ModelLineAdmin(admin.ModelAdmin):
#     ordering = ['name']
#     # Показать важные поля в списке объектов модели
#     list_display = ('name', 'default_output_type', 'brand')
#
#     fieldsets = (
#         ('Общая информация', {
#             'fields': (
#                 ('name', 'default_output_type', 'brand',), 'default_blinker')
#         }),
#         ('Опции', {
#             'fields': (
#                 ('default_ip', 'allowed_ip'), ('default_exd', 'allowed_exd'),
#                 ('default_body_coating', 'allowed_body_coating'),
#                 ('default_temperature', 'allowed_temperature'),
#                 ('default_control_unit_installed', 'allowed_control_unit_installed'),)
#         }),
#         ('Конечные, путевые выключатели и датчики момента', {
#             'fields': (
#                 ('default_end_switches', 'allowed_end_switches'), ('default_way_switches', 'allowed_way_switches'),
#                 ('default_torque_switches', 'allowed_torque_switches'))
#         }),
#         ('Прочее', {
#             'fields': (
#                 ('default_hand_wheel', 'allowed_hand_wheel'), ('default_operating_mode', 'allowed_operating_mode'),
#                 )
#         }),
#     )
#

class ElectricOperatingModeOptionInline(admin.TabularInline):
    """Inline для режима работы"""
    model = ElectricOperatingModeOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['operating_mode_option','encoding', 'is_default', 'is_active', 'sorting_order']
    verbose_name = _("Режим работы")
    verbose_name_plural = _("Опции режима работы")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        # Патчим метод __str__ для формы
        original_str = formset.model.__str__

        def safe_str(instance):
            try:
                return original_str(instance)
            except Exception as e:
                logger.debug(f"Ошибка в __str__: {e}")
                return "Новая опция"

        formset.model.__str__ = safe_str
        return formset
class ElectricMechanicalIndicatorOptionInline(admin.TabularInline):
    """Inline для механического индикатора"""
    model = ElectricMechanicalIndicatorOption
    extra = 0
    ordering = ['sorting_order']
    fields = [ 'mechanical_indicator_option', 'encoding', 'is_default', 'is_active', 'sorting_order']
    verbose_name = _("Механический индикатор")
    verbose_name_plural = _("Опции механического индикатора")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        # Патчим метод __str__ для формы
        original_str = formset.model.__str__

        def safe_str(instance):
            try:
                return original_str(instance)
            except Exception as e:
                logger.debug(f"Ошибка в __str__: {e}")
                return "Новая опция"

        formset.model.__str__ = safe_str
        return formset
class ElectricControlUnitInstalledOptionInline(admin.TabularInline) :
    """Inline для напряжения питания"""
    model = ElectricControlUnitInstalledOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['control_unit_option', 'encoding' ,  'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Блок управления")
    verbose_name_plural = _("Опции блоков управления")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        # Патчим метод __str__ для формы
        original_str = formset.model.__str__

        def safe_str(instance):
            try:
                return original_str(instance)
            except Exception as e:
                logger.debug(f"Ошибка в __str__: {e}")
                return "Новая опция"

        formset.model.__str__ = safe_str
        return formset


class ElectricBlinkerOptionInline(admin.TabularInline) :
    """Inline для температурных опций"""
    model = ElectricBlinkerOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['blinker_option' , 'encoding' ,   'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Блинкер")
    verbose_name_plural = _("Опции блинкера")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        # Патчим метод __str__ для формы
        original_str = formset.model.__str__

        def safe_str(instance):
            try:
                return original_str(instance)
            except Exception as e:
                logger.debug(f"Ошибка в __str__: {e}")
                return "Новая опция"

        formset.model.__str__ = safe_str
        return formset
class ElectricTurnAngleOptionInline(admin.TabularInline) :
    """Inline для опций угла поворота"""
    model = ElectricTurnAngleOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['encoding' , 'turn_angle', 'turn_angle_deviation_limit', 'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Угол поворота")
    verbose_name_plural = _("Опции угла поворота")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        # Патчим метод __str__ для формы
        original_str = formset.model.__str__

        def safe_str(instance):
            try:
                return original_str(instance)
            except Exception as e:
                logger.debug(f"Ошибка в __str__: {e}")
                return "Новая опция"

        formset.model.__str__ = safe_str
        return formset

class ElectricTemperatureOptionInline(admin.TabularInline) :
    """Inline для температурных опций"""
    model = ElectricTemperatureOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['encoding' , 'work_temp_min' , 'work_temp_max' , 'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Температурная опция")
    verbose_name_plural = _("Температурные опции")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        # Патчим метод __str__ для формы
        original_str = formset.model.__str__

        def safe_str(instance):
            try:
                return original_str(instance)
            except Exception as e:
                logger.debug(f"Ошибка в __str__: {e}")
                return "Новая опция"

        formset.model.__str__ = safe_str
        return formset

class ElectricIpOptionInline(admin.TabularInline) :
    """Inline для IP опций"""
    model = ElectricIpOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['ip_option' , 'encoding' ,  'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("IP опция")
    verbose_name_plural = _("IP опции")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        # Патчим метод __str__ для формы
        original_str = formset.model.__str__

        def safe_str(instance):
            try:
                return original_str(instance)
            except Exception as e:
                logger.debug(f"Ошибка в __str__: {e}")
                return "Новая опция"

        formset.model.__str__ = safe_str
        return formset
class ElectricBodyColorOptionInline(admin.TabularInline) :
    """Inline для ElectricHandWheelOption опций"""
    model = ElectricBodyColorOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['color_option' ,  'encoding' , 'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Опция цвета корпуса")
    verbose_name_plural = _("Опции цвета корпуса")

class ElectricHandWheelOptionInline(admin.TabularInline) :
    """Inline для PneumaticHandWheelOption опций"""
    model = ElectricHandWheelOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['hand_wheel_option' ,  'encoding' , 'is_default' , 'is_active' , 'sorting_order']
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

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        # Патчим метод __str__ для формы
        original_str = formset.model.__str__

        def safe_str(instance):
            try:
                return original_str(instance)
            except Exception as e:
                logger.debug(f"Ошибка в __str__: {e}")
                return "Новая опция"

        formset.model.__str__ = safe_str
        return formset

class ElectricBodyCoatingOptionInline(admin.TabularInline) :
    """Inline для опций покрытия корпуса"""
    model = ElectricBodyCoatingOption
    extra = 0
    ordering = ['sorting_order']
    fields = ['body_coating_option' , 'encoding' , 'is_default' , 'is_active' , 'sorting_order']
    verbose_name = _("Опция покрытия")
    verbose_name_plural = _("Опции покрытия")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)

        # Патчим метод __str__ для формы
        original_str = formset.model.__str__

        def safe_str(instance):
            try:
                return original_str(instance)
            except Exception as e:
                logger.debug(f"Ошибка в __str__: {e}")
                return "Новая опция"

        formset.model.__str__ = safe_str
        return formset


class AllowedControlUnitOptionInline(admin.TabularInline) :
    """Inline для разрешённых БУ серии"""
    model = AllowedControlUnitOption
    fk_name = 'model_line'
    extra = 0
    ordering = ['sorting_order']
    fields = ['control_unit' , 'encoding' , 'is_active' , 'sorting_order']
    verbose_name = _("Разрешённый БУ")
    verbose_name_plural = _("Разрешённые БУ для серии")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        original_str = formset.model.__str__
        def safe_str(instance):
            try:
                return original_str(instance)
            except Exception as e:
                logger.debug(f"Ошибка в __str__ AllowedControlUnitOption: {e}")
                return "Новая опция"
        formset.model.__str__ = safe_str
        return formset


class AllowedTurnCounterOptionInline(admin.TabularInline) :
    """Inline для разрешённых счётчиков серии"""
    model = AllowedTurnCounterOption
    fk_name = 'model_line'
    extra = 0
    ordering = ['sorting_order']
    fields = ['turn_counter' , 'encoding' , 'is_active' , 'sorting_order']
    verbose_name = _("Разрешённый счётчик")
    verbose_name_plural = _("Разрешённые счётчики для серии")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        original_str = formset.model.__str__
        def safe_str(instance):
            try:
                return original_str(instance)
            except Exception as e:
                logger.debug(f"Ошибка в __str__ AllowedTurnCounterOption: {e}")
                return "Новая опция"
        formset.model.__str__ = safe_str
        return formset


class AllowedSignalProfileOptionInline(admin.TabularInline) :
    """Inline для разрешённых профилей сигналов серии"""
    model = AllowedSignalProfileOption
    fk_name = 'model_line'
    extra = 0
    ordering = ['sorting_order']
    fields = ['signal_profile' , 'encoding' , 'is_active' , 'sorting_order']
    verbose_name = _("Разрешённый профиль сигналов")
    verbose_name_plural = _("Разрешённые профили сигналов для серии")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        original_str = formset.model.__str__
        def safe_str(instance):
            try:
                return original_str(instance)
            except Exception as e:
                logger.debug(f"Ошибка в __str__ AllowedSignalProfileOption: {e}")
                return "Новая опция"
        formset.model.__str__ = safe_str
        return formset


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
    # ]

    # Inline для всех типов опций
    inlines = [
        ElectricTemperatureOptionInline ,
        ElectricIpOptionInline ,
        ElectricExdOptionInline ,
        ElectricHandWheelOptionInline ,
        ElectricBodyCoatingOptionInline ,
        ElectricTurnAngleOptionInline ,
        ElectricBlinkerOptionInline ,
        # ElectricWaySwitchesOptionInline ,
        # ElectricControlUnitInstalledOptionInline ,
        # ElectricOperatingModeOptionInline ,  # ДОБАВИТЬ
        ElectricMechanicalIndicatorOptionInline,
        ElectricBodyColorOptionInline ,
        AllowedControlUnitOptionInline ,
        AllowedTurnCounterOptionInline ,
        AllowedSignalProfileOptionInline ,
    ]
    filter_horizontal = ('allowed_operating_mode',)  # ← добавить
    fieldsets = (
        (_('Основная информация') , {
            'fields' : (
                ('name' , 'code' , 'brand' , 'default_output_type') ,
                'model_item_code_template' ,'motor_thermal_protection',
                'description'
            )
        }) ,
        (_('Режим работы') , {
            'fields' : ('allowed_operating_mode' ,)  # ← Это ManyToManyField
        }) ,
        (_('Настройки') , {
            'fields' : ('sorting_order' , 'is_active')
        }) ,
    )
    # Добавляем действие копирования
    actions = [copy_electric_actuator_model_line]

    def get_queryset(self, request):
        """Оптимизация запросов с учетом through-моделей"""
        return super().get_queryset(request).select_related(
            'brand',
            'default_output_type',
        ).prefetch_related(
            'temperature_options',
            'ip_options',
            'exd_options',
            'body_coating_options',
            'hand_wheel_options',
            'turn_angle_options',
            'blinker_options',
            # 'way_switches_options',
            'control_unit_options',
            # 'operating_mode_options',
            'allowed_control_units',
            'allowed_turn_counters',
            'allowed_signal_profiles',
            'mechanical_indicator_options'
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
        """Сохраняем модель БЕЗ создания опций"""
        super().save_model(request , obj , form , change)
        # НЕ создаем опции здесь

    def save_formset(self, request, form, formset, change):
        """Сохраняем inline формы и создаем недостающие опции ПОСЛЕ"""

        super().save_formset(request, form, formset, change)

        if not change:
            parent_obj = form.instance

            # Проверяем, что parent_obj сохранен
            if parent_obj and parent_obj.pk:
                option_models = [
                    ElectricTemperatureOption,
                    ElectricIpOption,
                    ElectricExdOption,
                    # ... другие
                ]

                for model_class in option_models:
                    parent_field = getattr(model_class, '_get_parent_field_name', lambda: None)()
                    if parent_field:
                        existing_count = model_class.objects.filter(
                            **{parent_field: parent_obj}
                        ).count()

                        if existing_count == 0:
                            try:
                                if hasattr(model_class, 'ensure_default_exists'):
                                    model_class.ensure_default_exists(parent_obj)
                            except Exception as e:
                                # Если ошибка связана с отсутствием parent, игнорируем
                                if "must be saved" in str(e) or "doesn't have a primary key" in str(e):
                                    logger.debug(f"Parent not saved yet, skipping {model_class.__name__}")
                                else:
                                    logger.error(f"Ошибка создания опции {model_class.__name__}: {e}")

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

    def add_view(self, request, form_url='', extra_context=None):
        """Отладочный вывод при создании объекта"""
        logger.debug("=== НАЧАЛО add_view ===")
        try:
            return super().add_view(request, form_url, extra_context)
        except Exception as e:
            logger.error(f"Ошибка в add_view: {e}", exc_info=True)
            raise

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        """Отладочный вывод при рендеринге формы"""
        logger.debug(f"=== render_change_form: add={add}, change={change} ===")

        # Логируем информацию о связанных объектах
        if obj:
            logger.debug(f"Объект: {obj}, ID: {obj.id}")

        return super().render_change_form(request, context, add, change, form_url, obj)