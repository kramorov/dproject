# electric_actuators/admin/ea_actuator_selected_admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django import forms
from django.contrib import messages
from django.utils.html import format_html
from django.urls import reverse
from django.db import transaction
import logging

from electric_actuators.models.ea_actuator_selected import ElectricActuatorSelected

logger = logging.getLogger(__name__)


# ============================= КАСТОМНАЯ ФОРМА =============================

class ElectricActuatorSelectedForm(forms.ModelForm) :
    """Кастомная форма для выбранного электропривода"""

    class Meta :
        model = ElectricActuatorSelected
        fields = '__all__'
        widgets = {
            'description' : forms.Textarea(attrs={'rows' : 3}) ,
        }

    def __init__(self , *args , **kwargs) :
        super().__init__(*args , **kwargs)

        instance = kwargs.get('instance')

        # Если есть выбранная модель, фильтруем доступные опции
        if instance and instance.selected_model_line_item :
            self._filter_options_by_model_line(instance.selected_model_line_item)

        # Добавляем классы CSS для улучшения UX
        for field_name , field in self.fields.items() :
            if field_name.startswith('selected_') or field_name.startswith('actual_') :
                field.widget.attrs['class'] = 'option-field'

    def _filter_options_by_model_line(self , model_line_item) :
        """Фильтрует опции по выбранной модели"""

        # Получаем связанную серию (model_line)
        model_line = model_line_item.model_line

        # Фильтруем каждое поле опций
        for option_field , config in ElectricActuatorSelected._OPTION_CONFIG.items() :
            if option_field in self.fields :
                parent_field = config['parent_field']

                # Импортируем модель опции
                try :
                    module_path , class_name = config['model_path'].rsplit('.' , 1)
                    module = __import__(module_path , fromlist=[class_name])
                    model_class = getattr(module , class_name)

                    # Строим фильтр
                    filter_kwargs = {f"{parent_field}" : model_line}

                    # Если это температура, возможно нужен другой фильтр
                    if option_field == 'selected_temperature' :
                        # Для температуры может быть прямая связь с model_line
                        filter_kwargs = {"model_line" : model_line}

                    # Получаем доступные опции
                    available_options = model_class.objects.filter(**filter_kwargs , is_active=True)

                    # Устанавливаем queryset для поля
                    self.fields[option_field].queryset = available_options

                    # Устанавливаем пустое значение
                    self.fields[option_field].empty_label = "--- Выберите опцию ---"

                except Exception as e :
                    logger.error(f"Ошибка фильтрации опций {option_field}: {e}")


# ============================= INLINE ДЛЯ СВЯЗАННЫХ ДАННЫХ =============================

class ElectricActuatorMountingPlateInline(admin.TabularInline) :
    """Inline для монтажных площадок"""
    model = ElectricActuatorSelected.actual_mounting_plate.through
    extra = 1
    verbose_name = _("Монтажная площадка")
    verbose_name_plural = _("Монтажные площадки")

    # Автодополнение для ForeignKey
    # autocomplete_fields = ['mountingplatetypes']

    def get_formset(self , request , obj=None , **kwargs) :
        formset = super().get_formset(request , obj , **kwargs)

        # Лимитируем выбор, если нужно
        return formset


# ============================= ОСНОВНАЯ АДМИНКА =============================

@admin.register(ElectricActuatorSelected)
class ElectricActuatorSelectedAdmin(admin.ModelAdmin) :
    """Админка для выбранных конфигураций электроприводов"""

    form = ElectricActuatorSelectedForm

    # ========== НАСТРОЙКИ ОТОБРАЖЕНИЯ СПИСКА ==========
    list_display = [
        'name' ,
        'code' ,
        'model_line_item_display' ,
        'selected_options_display' ,
        'is_active_badge' ,
        'is_unique_display' ,
        'sorting_order'
    ]

    list_editable = ['sorting_order']
    list_display_links = ['name']

    list_filter = [
        'is_active' ,
        'is_unique' ,
        'selected_model_line_item__model_line' ,
    ]

    search_fields = [
        'name' ,
        'code' ,
        'description' ,
        'selected_model_line_item__name' ,
        'selected_model_line_item__code' ,
    ]

    list_per_page = 30
    list_select_related = [
        'selected_model_line_item' ,
        'selected_model_line_item__model_line' ,
        'selected_temperature' ,
        'selected_ip' ,
        'selected_exd' ,
        'selected_body_coating' ,
        'selected_hand_wheel' ,
        'selected_safety_position' ,
    ]

    # ========== ПОЛЯ В ФОРМЕ РЕДАКТИРОВАНИЯ ==========
    fieldsets = (
        (_('Основная информация') , {
            'fields' : (
                ('name' , 'code') ,
                'description' ,
            ) ,
            'classes' : ('wide' ,)
        }) ,
        (_('Базовая модель') , {
            'fields' : (
                'selected_model_line_item' ,
            ) ,
            'classes' : ('wide' ,)
        }) ,
        (_('Механические опции') , {
            'fields' : (
                'actual_stem_shape' ,
                'actual_stem_size' ,
                'actual_cable_glands_holes' ,
            ) ,
            'classes' : ('collapse' , 'wide')
        }) ,
        (_('Электрические опции') , {
            'fields' : (
                'selected_safety_position' ,
                'selected_temperature' ,
                'selected_ip' ,
                'selected_exd' ,
                'selected_body_coating' ,
                'selected_hand_wheel' ,
            ) ,
            'classes' : ('wide' ,)
        }) ,
        (_('Статусы и настройки') , {
            'fields' : (
                ('is_active' , 'is_unique') ,
                'sorting_order' ,
            ) ,
            'classes' : ('collapse' ,)
        }) ,
    )

    # ========== АВТОДОПОЛНЕНИЕ ==========
    # autocomplete_fields = [
    #     'selected_model_line_item' ,
    #     'actual_stem_shape' ,
    #     'actual_stem_size' ,
    #     'actual_cable_glands_holes' ,
    #     'selected_safety_position' ,
    # ]

    # Используем raw_id_fields для опций, которые фильтруются в форме
    raw_id_fields = [
        'selected_temperature' ,
        'selected_ip' ,
        'selected_exd' ,
        'selected_body_coating' ,
        'selected_hand_wheel' ,
    ]

    # ========== INLINES ==========
    inlines = [ElectricActuatorMountingPlateInline]

    # ========== ДЕЙСТВИЯ ==========
    actions = [
        'set_as_unique' ,
        'set_as_not_unique' ,
        'apply_default_options' ,
        'generate_names_and_codes' ,
    ]

    def set_as_unique(self , request , queryset) :
        """Пометить как уникальную конфигурацию"""
        updated = queryset.update(is_unique=True)
        self.message_user(
            request ,
            f"{updated} конфигураций помечены как уникальные." ,
            messages.SUCCESS
        )

    set_as_unique.short_description = _("Пометить как уникальные")

    def set_as_not_unique(self , request , queryset) :
        """Пометить как не уникальную конфигурацию"""
        updated = queryset.update(is_unique=False)
        self.message_user(
            request ,
            f"{updated} конфигураций помечены как не уникальные." ,
            messages.SUCCESS
        )

    set_as_not_unique.short_description = _("Пометить как не уникальные")

    def apply_default_options(self , request , queryset) :
        """Применить дефолтные опции из выбранной модели"""
        success_count = 0
        error_count = 0

        for selected_actuator in queryset :
            try :
                with transaction.atomic() :
                    if selected_actuator.selected_model_line_item :
                        # Применяем дефолтные опции
                        selected_actuator.apply_default_options()
                        selected_actuator.save()
                        success_count += 1
                        logger.info(f"Применены дефолтные опции для: {selected_actuator.name}")
                    else :
                        error_count += 1
                        logger.warning(f"Нет выбранной модели для: {selected_actuator.name}")

            except Exception as e :
                error_count += 1
                logger.error(f"Ошибка применения опций для {selected_actuator}: {e}")

        if success_count > 0 :
            messages.success(request , f"Применены дефолтные опции для {success_count} конфигураций.")
        if error_count > 0 :
            messages.warning(request , f"Не удалось применить опции для {error_count} конфигураций.")

    apply_default_options.short_description = _("Применить дефолтные опции")

    def generate_names_and_codes(self , request , queryset) :
        """Сгенерировать названия и коды"""
        success_count = 0

        for selected_actuator in queryset :
            try :
                # Вызываем метод модели для генерации
                selected_actuator.generate_name_and_code()
                selected_actuator.save()
                success_count += 1
                logger.info(f"Сгенерировано имя и код для: {selected_actuator.name}")
            except Exception as e :
                logger.error(f"Ошибка генерации для {selected_actuator}: {e}")

        messages.success(request , f"Сгенерированы имена и коды для {success_count} конфигураций.")

    generate_names_and_codes.short_description = _("Сгенерировать названия и коды")

    # ========== МЕТОДЫ ДЛЯ ОТОБРАЖЕНИЯ В СПИСКЕ ==========

    def model_line_item_display(self , obj) :
        """Отображение выбранной модели"""
        if obj.selected_model_line_item :
            url = reverse(
                'admin:electric_actuators_electricactuatormodellineitem_change' ,
                args=[obj.selected_model_line_item.id]
            )
            return format_html(
                '<a href="{}"><strong>{}</strong></a><br>'
                '<small>Серия: {}</small>' ,
                url ,
                obj.selected_model_line_item.name ,
                obj.selected_model_line_item.model_line.name if obj.selected_model_line_item.model_line else '-'
            )
        return "-"

    model_line_item_display.short_description = _("Модель")
    model_line_item_display.admin_order_field = 'selected_model_line_item__name'

    def selected_options_display(self , obj) :
        """Компактное отображение выбранных опций"""
        options = []

        # Список опций для отображения
        option_fields = [
            ('selected_temperature' , '🌡️') ,
            ('selected_ip' , '🛡️') ,
            ('selected_exd' , '💥') ,
            ('selected_body_coating' , '🎨') ,
            ('selected_hand_wheel' , '🔄') ,
        ]

        for field_name , icon in option_fields :
            option = getattr(obj , field_name)
            if option :
                options.append(f"{icon} {str(option)[:15]}")

        if options :
            return format_html(
                '<div style="display: flex; flex-wrap: wrap; gap: 3px;">{}</div>' ,
                ''.join([f'<span style="background: #e9ecef; padding: 2px 5px; border-radius: 3px;">{opt}</span>'
                         for opt in options])
            )
        return "-"

    selected_options_display.short_description = _("Выбранные опции")

    def is_active_badge(self , obj) :
        """Отображение статуса активности"""
        if obj.is_active :
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Активно</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Неактивно</span>'
        )

    is_active_badge.short_description = _("Статус")
    is_active_badge.allow_tags = True

    def is_unique_display(self , obj) :
        """Отображение уникальности"""
        if obj.is_unique :
            return format_html(
                '<span style="color: #17a2b8; font-weight: bold;">★ Уникальная</span>'
            )
        return format_html(
            '<span style="color: #6c757d;">Стандартная</span>'
        )

    is_unique_display.short_description = _("Уникальность")
    is_unique_display.allow_tags = True

    # ========== МЕТОДЫ СОХРАНЕНИЯ ==========

    def save_model(self , request , obj , form , change) :
        """Сохранение модели с автоматическим заполнением дефолтных значений"""

        # Если создается новый объект и выбрана модель
        if not change and obj.selected_model_line_item :
            # Применяем дефолтные опции
            obj.apply_default_options()

            # Генерируем имя и код, если они пустые
            if not obj.name :
                obj.generate_name_and_code()

        # Сохраняем модель
        super().save_model(request , obj , form , change)

        # Логируем действие
        action = "обновлена" if change else "создана"
        logger.info(
            f"Конфигурация электропривода {action}: "
            f"ID={obj.id}, Модель={obj.selected_model_line_item}, "
            f"Уникальная={obj.is_unique}"
        )

    def get_form(self , request , obj=None , **kwargs) :
        """Получение формы с динамической фильтрацией"""
        form = super().get_form(request , obj , **kwargs)

        # Для существующего объекта фильтруем опции
        if obj and obj.selected_model_line_item :
            # Динамически фильтруем queryset для полей опций
            model_line = obj.selected_model_line_item.model_line

            for option_field , config in ElectricActuatorSelected._OPTION_CONFIG.items() :
                if option_field in form.base_fields :
                    try :
                        module_path , class_name = config['model_path'].rsplit('.' , 1)
                        module = __import__(module_path , fromlist=[class_name])
                        model_class = getattr(module , class_name)

                        # Фильтруем по model_line
                        filter_kwargs = {f"{config['parent_field']}" : model_line}
                        queryset = model_class.objects.filter(**filter_kwargs , is_active=True)

                        form.base_fields[option_field].queryset = queryset

                    except Exception as e :
                        logger.error(f"Ошибка фильтрации поля {option_field}: {e}")

        return form

    def response_change(self , request , obj) :
        """Обработка после изменения"""

        # Показываем сообщение, если были применены дефолтные опции
        if 'apply_defaults' in request.POST :
            messages.success(request , _("Дефолтные опции успешно применены."))

        return super().response_change(request , obj)

    # ========== КАСТОМНЫЕ ВЬЮХИ ==========

    def change_view(self , request , object_id , form_url='' , extra_context=None) :
        """Кастомный вид редактирования"""
        extra_context = extra_context or {}
        extra_context['title'] = _("Редактирование конфигурации электропривода")

        # Добавляем кнопку для применения дефолтных опций
        extra_context['show_apply_defaults'] = True

        return super().change_view(request , object_id , form_url , extra_context)

    def add_view(self , request , form_url='' , extra_context=None) :
        """Кастомный вид добавления"""
        extra_context = extra_context or {}
        extra_context['title'] = _("Создание новой конфигурации электропривода")
        extra_context['help_text'] = _(
            "После выбора модели будут автоматически применены дефолтные опции "
            "и сгенерированы название и код."
        )

        return super().add_view(request , form_url , extra_context)

    # ========== ПРОИЗВОДИТЕЛЬНОСТЬ ==========

    def get_queryset(self , request) :
        """Оптимизированный запрос"""
        qs = super().get_queryset(request)

        return qs.select_related(
            'selected_model_line_item' ,
            'selected_model_line_item__model_line' ,
            'selected_model_line_item__model_line__brand' ,
            'selected_temperature' ,
            'selected_ip' ,
            'selected_exd' ,
            'selected_body_coating' ,
            'selected_hand_wheel' ,
            'selected_safety_position' ,
            'actual_stem_shape' ,
            'actual_stem_size' ,
            'actual_cable_glands_holes' ,
        ).prefetch_related(
            'actual_mounting_plate' ,
        )

    # ========== JavaScript для динамической фильтрации ==========

    class Media :
        js = (
            'admin/js/vendor/jquery/jquery.js' ,
            'admin/js/jquery.init.js' ,
            'admin/js/electric_selected_admin.js' ,  # Кастомный JS файл
        )
        css = {
            'all' : ('admin/css/electric_selected_admin.css' ,)
        }