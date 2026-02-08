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
        model_line = model_line_item.model_line

        # Фильтруем каждое поле опций
        for option_field , config in ElectricActuatorSelected._OPTION_CONFIG.items() :
            if option_field in self.fields :
                parent_field = config['parent_field']

                try :
                    # Динамический импорт модели
                    import importlib
                    module_path , class_name = config['model_path'].rsplit('.' , 1)
                    module = importlib.import_module(module_path)
                    model_class = getattr(module , class_name)

                    # Строим фильтр
                    filter_kwargs = {parent_field : model_line}

                    # Получаем доступные опции
                    available_options = model_class.objects.filter(**filter_kwargs , is_active=True)

                    # Устанавливаем queryset для поля
                    self.fields[option_field].queryset = available_options
                    self.fields[option_field].empty_label = "--- Выберите опцию ---"

                except Exception as e :
                    logger.error(f"Ошибка фильтрации опций {option_field}: {e}")
                    # Пропускаем, оставляем оригинальный queryset
                    continue


# ============================= INLINE ДЛЯ СВЯЗАННЫХ ДАННЫХ =============================

class ElectricActuatorMountingPlateInline(admin.TabularInline) :
    """Inline для монтажных площадок"""
    model = ElectricActuatorSelected.actual_mounting_plate.through
    extra = 1
    verbose_name = _("Монтажная площадка")
    verbose_name_plural = _("Монтажные площадки")

    def get_formset(self , request , obj=None , **kwargs) :
        return super().get_formset(request , obj , **kwargs)


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
        # 'selected_safety_position',  # Убрать, если нет в модели
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
        'apply_default_options' ,
        'generate_names_and_codes' ,
    ]

    def apply_default_options(self , request , queryset) :
        """Применить дефолтные опции из выбранной модели"""
        success_count = 0
        error_count = 0

        for selected_actuator in queryset :
            try :
                with transaction.atomic() :
                    if selected_actuator.selected_model_line_item :
                        selected_actuator.apply_default_options()
                        selected_actuator.save()
                        success_count += 1
                        logger.info(f"Применены дефолтные опции для: {selected_actuator.name}")
                    else :
                        error_count += 1
                        logger.warning(f"Нет выбранной модели для: {selected_actuator.name}")
                        self.message_user(
                            request ,
                            f"Нет выбранной модели для {selected_actuator.name}" ,
                            messages.WARNING
                        )

            except Exception as e :
                error_count += 1
                logger.error(f"Ошибка применения опций для {selected_actuator}: {e}")
                self.message_user(
                    request ,
                    f"Ошибка для {selected_actuator.name}: {str(e)[:100]}" ,
                    messages.ERROR
                )

        if success_count > 0 :
            messages.success(request , f"Применены дефолтные опции для {success_count} конфигураций.")
        if error_count > 0 :
            messages.warning(request , f"Не удалось применить опции для {error_count} конфигураций.")

    apply_default_options.short_description = _("Применить дефолтные опции")

    def generate_names_and_codes(self , request , queryset) :
        """Сгенерировать названия и коды"""
        success_count = 0
        error_count = 0

        for selected_actuator in queryset :
            try :
                selected_actuator.generate_name_and_code()
                selected_actuator.save()
                success_count += 1
                logger.info(f"Сгенерировано имя и код для: {selected_actuator.name}")
            except Exception as e :
                error_count += 1
                logger.error(f"Ошибка генерации для {selected_actuator}: {e}")
                self.message_user(
                    request ,
                    f"Ошибка для {selected_actuator.name}: {str(e)[:100]}" ,
                    messages.ERROR
                )

        if success_count > 0 :
            messages.success(request , f"Сгенерированы имена и коды для {success_count} конфигураций.")
        if error_count > 0 :
            messages.warning(request , f"Не удалось сгенерировать для {error_count} конфигураций.")

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

        apply_defaults = request.POST.get('apply_defaults') == '1'
        generate_name_code = request.POST.get('generate_name_code') == '1'

        # ДЕБАГ: выводим все POST данные
        print("=" * 50)
        print("DEBUG save_model called")
        print(f"change: {change}")
        print(f"apply_defaults: {apply_defaults}")
        print(f"generate_name_code: {generate_name_code}")
        print(f"POST data: {dict(request.POST)}")
        print(f"selected_model_line_item: {obj.selected_model_line_item}")
        print("=" * 50)

        # Новая запись
        if not change :
            print("DEBUG: New record creation")
            if obj.selected_model_line_item :
                try :
                    print("DEBUG: Auto-applying default options")
                    obj.apply_default_options()
                    print(f"DEBUG: Default options applied")

                    if not obj.name :
                        print("DEBUG: Auto-generating name and code")
                        obj.generate_name_and_code()
                        print(f"DEBUG: Generated name: {obj.name}, code: {obj.code}")

                except Exception as e :
                    print(f"DEBUG ERROR: {e}")
                    logger.error(f"Ошибка при создании новой записи: {e}")
                    messages.error(request , f"Ошибка: {str(e)[:100]}")

        # Существующая запись с кнопкой "Применить дефолтные опции"
        elif change and apply_defaults :
            print(f"DEBUG: Applying defaults for existing record {obj.id}")
            if obj.selected_model_line_item :
                try :
                    obj.apply_default_options()
                    messages.success(request , _("Дефолтные опции успешно применены."))
                    print(f"DEBUG: Default options applied")
                except Exception as e :
                    print(f"DEBUG ERROR: {e}")
                    logger.error(f"Ошибка применения дефолтных опций: {e}")
                    messages.error(request , f"Ошибка применения дефолтных опций: {str(e)[:100]}")
            else :
                messages.error(request , _("Не выбрана модель для применения опций"))

        # Существующая запись с кнопкой "Сгенерировать имя и код"
        elif change and generate_name_code :
            print(f"DEBUG: Generating name/code for existing record {obj.id}")
            try :
                obj.generate_name_and_code()
                messages.success(request , _("Имя и код успешно сгенерированы."))
                print(f"DEBUG: Generated name: {obj.name}, code: {obj.code}")
            except Exception as e :
                print(f"DEBUG ERROR: {e}")
                logger.error(f"Ошибка генерации имени и кода: {e}")
                messages.error(request , f"Ошибка генерации имени и кода: {str(e)[:100]}")

        super().save_model(request , obj , form , change)

        print(f"DEBUG: Model saved, ID={obj.id}")

    def get_form(self , request , obj=None , **kwargs) :
        """Получение формы с динамической фильтрацией"""
        form = super().get_form(request , obj , **kwargs)

        if obj and obj.selected_model_line_item and obj.selected_model_line_item.model_line :
            model_line = obj.selected_model_line_item.model_line

            import importlib

            for option_field , config in ElectricActuatorSelected._OPTION_CONFIG.items() :
                if option_field in form.base_fields :
                    try :
                        module_path , class_name = config['model_path'].rsplit('.' , 1)
                        module = importlib.import_module(module_path)
                        model_class = getattr(module , class_name)

                        filter_kwargs = {config['parent_field'] : model_line}
                        queryset = model_class.objects.filter(**filter_kwargs , is_active=True)

                        form.base_fields[option_field].queryset = queryset

                    except Exception as e :
                        logger.error(f"Ошибка фильтрации поля {option_field}: {e}")
                        continue

        return form

    def add_view(self , request , form_url='' , extra_context=None) :
        """Кастомный вид добавления"""
        extra_context = extra_context or {}
        extra_context['title'] = _("Создание новой конфигурации электропривода")
        extra_context['help_text'] = _(
            "После выбора модели будут автоматически применены дефолтные опции "
            "и сгенерированы название и код."
        )
        return super().add_view(request , form_url , extra_context)

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
            'admin/js/electric_selected_admin.js' ,
        )
        css = {
            'all' : (
                'admin/css/electric_selected_admin.css' ,
            )
        }