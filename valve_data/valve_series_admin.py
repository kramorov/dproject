from django.contrib import admin
from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _

from params.models import BodyColor
from .models import ValveModelData , ValveLineSeries , \
    ValveSeriesAttributeValue , \
    ValveSeriesDnPnTorqueMountData , ValveLineEAVAttribute , ValveLineEAVValue , ValveLineEAVChoiceValue , \
    ValveLineEAVSection , ValveLineSeriesBodyColor
from .models_valve_line_properties import ValveConnectionToPipe , ValveVariety
from .models_eav import EAVAttribute , EAVValue , ValveVarietyAttribute
from .models_valve_line import ValveLine


def duplicate_selected_action(model_admin , request , queryset) :
    for obj in queryset :
        new_obj = obj.__class__()
        for field in obj._meta.fields :
            if field.name != 'id' :
                setattr(new_obj , field.name , getattr(obj , field.name))

        if hasattr(obj , 'symbolic_code') and isinstance(obj._meta.get_field('symbolic_code') , models.CharField) :
            new_obj.symbolic_code = f"{new_obj.symbolic_code}(K)"

        new_obj.pk = None
        new_obj.save()
        # Копирование ManyToMany полей
        for field in obj._meta.many_to_many:
            if field.name != 'id':
                original_m2m = getattr(obj, field.name)
                new_m2m = getattr(new_obj, field.name)
                for item in original_m2m.all():
                    new_m2m.add(item)

        # Специальная обработка для ValveSeriesAttributeValue
        if hasattr(obj, 'attribute_values'):
            for attr_value in obj.attribute_values.all():
                new_attr_value = ValveSeriesAttributeValue(
                    valve_series=new_obj,
                    attribute=attr_value.attribute,
                    predefined_value=attr_value.predefined_value,
                    custom_value=attr_value.custom_value
                )
                new_attr_value.save()
        if hasattr(obj , 'valve_model_mounting_plate') and isinstance(
                obj._meta.get_field('valve_model_mounting_plate') , models.ManyToManyField) :
            for mounting_plate in obj.valve_model_mounting_plate.all() :
                new_obj.valve_model_mounting_plate.add(mounting_plate)

    model_admin.message_user(request , "Выбранные записи успешно скопированы.")


class EAVValueInline(admin.TabularInline):
    """Inline для значений атрибута"""
    model = EAVValue
    extra = 1
    fields = ['value', 'display_name', 'order', 'is_active']


@admin.register(EAVAttribute)
class EAVAttributeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'data_type', 'unit', 'values_count']
    list_filter = ['data_type']
    search_fields = ['name', 'code', 'description']
    inlines = [EAVValueInline]

    def values_count(self, obj):
        return obj.possible_values.count()

    values_count.short_description = _("Количество значений")


@admin.register(EAVValue)
class EAVValueAdmin(admin.ModelAdmin) :
    """Админка для значений атрибутов"""
    list_display = ['attribute' , 'value' , 'display_name' , 'order' , 'is_active']
    list_filter = ['attribute' , 'is_active']
    search_fields = ['value' , 'display_name' , 'attribute__name']
    list_editable = ['order' , 'is_active']

    def get_urls(self) :
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('json-values/' , self.admin_site.admin_view(self.json_values) , name='valve_data_eavvalue_json') ,
        ]
        return custom_urls + urls

    def json_values(self , request) :
        """JSON endpoint для значений атрибутов"""
        from django.http import JsonResponse
        attribute_id = request.GET.get('attribute_id')
        if not attribute_id :
            attribute_id = request.GET.get('attribute__id')
        print(f"DEBUG: Received request for attribute_id: {attribute_id}")  # Отладочная информация
        if attribute_id :
            try :
                values = EAVValue.objects.filter(
                    attribute_id=int(attribute_id) ,
                    is_active=True
                ).order_by('order' , 'display_name')
                print(f"DEBUG: Found {values.count()} values for attribute {attribute_id}")  # Отладочная информация
                data = [{'id' : v.id , 'text' : v.display_name} for v in values]
                return JsonResponse(data , safe=False)
            except (ValueError , TypeError) :
                # print(f"DEBUG: Error: {e}")  # Отладочная информация
                return JsonResponse([] , safe=False)
        return JsonResponse([] , safe=False)

class ValveSeriesAttributeValueForm(forms.ModelForm):
#     """Упрощенная форма для значений атрибутов серии"""

    class Meta:
        model = ValveSeriesAttributeValue
        fields = '__all__'
        widgets = {
            'custom_value': forms.TextInput(attrs={'placeholder': _('Введите произвольное значение...')}),
            'attribute': forms.Select(attrs={'class': 'attribute-select'}),
            'predefined_value': forms.Select(attrs={'class': 'predefined-value-select'}),
        }

    def __init__(self, *args, **kwargs):
        # Извлекаем parent_obj из kwargs
        self.parent_obj = kwargs.pop('parent_obj', None)
        super().__init__(*args, **kwargs)

        print(f"DEBUG FORM: instance pk: {getattr(self.instance, 'pk', None)}")
        print(f"DEBUG FORM: parent_obj: {self.parent_obj}")

        # Если есть instance с attribute_id - фильтруем значения
        if self.instance and self.instance.pk and self.instance.attribute_id:
            self.fields['predefined_value'].queryset = EAVValue.objects.filter(
                attribute_id=self.instance.attribute_id,
                is_active=True
            ).order_by('order', 'display_name')
            print(f"DEBUG FORM: Limited values for existing attribute: {self.instance.attribute_id}")
        else:
            # Для новых записей - пустой список
            self.fields['predefined_value'].queryset = EAVValue.objects.none()
            print(f"DEBUG FORM: Empty values for new instance")

        # Делаем поля необязательными
        self.fields['predefined_value'].required = False
        self.fields['custom_value'].required = False

    def clean(self):
        """Валидация формы"""
        cleaned_data = super().clean()
        predefined_value = cleaned_data.get('predefined_value')
        custom_value = cleaned_data.get('custom_value')
        attribute = cleaned_data.get('attribute')

        # Проверяем, что заполнено только одно значение
        if predefined_value and custom_value:
            raise forms.ValidationError(_("Можно указать только одно значение: либо из справочника, либо произвольное"))

        # Проверяем соответствие predefined_value и attribute
        if predefined_value and attribute and predefined_value.attribute != attribute:
            raise forms.ValidationError(_("Выбранное значение не соответствует атрибуту"))

        return cleaned_data


class ValveSeriesAttributeValueInline(admin.TabularInline):
    """Inline для значений атрибутов серии"""
    model = ValveSeriesAttributeValue
    form = ValveSeriesAttributeValueForm
    extra = 1
    verbose_name = _("Атрибут серии")
    verbose_name_plural = _("Атрибуты серии")
    autocomplete_fields = []

    def get_formset(self, request, obj=None, **kwargs):
        """Передаем контекст в формы"""
        print(f"DEBUG: ValveSeriesAttributeValueInline get_formset called with obj: {obj}")

        # Сохраняем родительский объект
        self.parent_obj = obj

        # Используем кастомный FormSet для передачи данных
        FormSet = super().get_formset(request, obj, **kwargs)

        # Создаем кастомный FormSet с поддержкой parent_obj
        class CustomFormSet(FormSet):
            def __init__(self, *args, **kwargs):
                self.parent_obj = obj  # Передаем parent_obj в FormSet
                super().__init__(*args, **kwargs)

            def _construct_form(self, i, **kwargs):
                # Передаем parent_obj в каждую форму
                kwargs['parent_obj'] = self.parent_obj
                return super()._construct_form(i, **kwargs)

        return CustomFormSet

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Ограничиваем выбор в зависимости от контекста"""
        print(f"DEBUG: ValveSeriesAttributeValueInline formfield_for_foreignkey for db_field.name={db_field.name}")

        if db_field.name == "attribute":
            # Ограничиваем атрибуты для родительского объекта
            if hasattr(self, 'parent_obj') and self.parent_obj:
                if self.parent_obj.valve_line and self.parent_obj.valve_line.valve_variety:
                    valve_variety = self.parent_obj.valve_line.valve_variety
                    allowed_attributes = valve_variety.allowed_attributes.values_list('attribute_id', flat=True)
                    kwargs["queryset"] = EAVAttribute.objects.filter(id__in=allowed_attributes)
                    print(f"DEBUG: Limited attributes for variety: {valve_variety}")

        elif db_field.name == "predefined_value":
            print(f"# Изначально пустой queryset - будет обновляться через JavaScript")
            kwargs["queryset"] = EAVValue.objects.none()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    class Media:
        js = (
            'admin/js/jquery.init.js',
            'js/valve_series_attributes.js',
        )


class ValveLineSeriesBodyColorInline(admin.TabularInline) :
    """Inline для цветов корпуса серии"""
    model = ValveLineSeriesBodyColor
    extra = 1
    verbose_name = _("Цвет корпуса")
    verbose_name_plural = _("Цвета корпусов")

    def formfield_for_foreignkey(self , db_field , request , **kwargs) :
        """Ограничиваем выбор в зависимости от поля"""
        if db_field.name == "body_color" :
            kwargs["queryset"] = BodyColor.objects.filter(is_active=True).order_by('sorting_order' , 'name')
        # elif db_field.name == "option_variety" :
            # kwargs["queryset"] = BodyColorExecutionType.objects.filter(is_active=True).order_by('sorting_order' ,
            #                                                                                     'name')
        return super().formfield_for_foreignkey(db_field , request , **kwargs)


class ValveLineSeriesAdmin(admin.ModelAdmin):
    ordering = ['symbolic_code', 'valve_line']
    fieldsets = (
        (_('Серия, семейство арматуры, присоединение'), {
            'fields': (
                ('symbolic_code', 'valve_line','pipe_connection'),
            )
        }),
        (_('Материалы'), {
            'fields': (
                ('body_material', 'body_material_specified'),
                ('shut_element_material', 'shut_element_material_specified'),
                'sealing_element_material_specified',)
        }),
        (_('Цвета корпуса') , {
            'fields' : () ,
            'description' : _('Цвета корпуса настраиваются через вкладку "Цвета корпусов" ниже')
        }) ,
        (_('Диапазон температур'), {
            'fields': (
                ('work_temp_min', 'work_temp_max'), ('temp_min', 'temp_max'),
            )
        }),
    )
    list_display = (
        'get_display_code' ,  # Заменяем symbolic_code на кастомный метод (определен ниже)
        'valve_line' ,
        'body_material' ,
        'body_material_specified' ,
        'shut_element_material' ,
        'shut_element_material_specified' ,
        'sealing_element_material_specified' ,
        'temp_min' ,
        'temp_max' ,
        'work_temp_min' ,
        'work_temp_max' ,
        'pipe_connection'
    )
    search_fields = ['symbolic_code', 'valve_line__symbolic_code']
    # list_select_related = ('valve_line', 'body_material', 'body_material_specified',
    #                       'shut_element_material', 'shut_element_material_specified',
    #                       'sealing_element_material_specified', 'pipe_connection')
    # Правильно - используем list_filter для связанных полей
    list_filter = (
        'valve_line__valve_variety' ,  # Фильтр по типу арматуры
        'valve_line' ,
        'body_material' ,
        'pipe_connection'
    )
    inlines = [ValveSeriesAttributeValueInline , ValveLineSeriesBodyColorInline]
    actions = [duplicate_selected_action]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'valve_line__valve_variety',
            'valve_line__valve_brand',
            'valve_line',
            'body_material',
            'body_material_specified',
            'shut_element_material',
            'shut_element_material_specified',
            'sealing_element_material_specified',
            'pipe_connection'
        ).prefetch_related('body_colors')



    def get_display_code(self , obj) :
        """Безопасное формирование строки с проверкой на None"""
        parts = []

        if obj.valve_line and obj.valve_line.valve_brand :
            parts.append(str(obj.valve_line.valve_brand))

        if obj.valve_line and obj.valve_line.symbolic_code :
            parts.append(str(obj.valve_line.symbolic_code))

        if obj.symbolic_code :
            parts.append(str(obj.symbolic_code))

        if len(parts) >= 3 :
            return f"{parts[0]}-{parts[1]}-{parts[2]}"
        elif parts :
            return "-".join(parts)
        else :
            return _("Не указано")

    def get_form(self, request, obj=None, **kwargs):
        """Передаем объект в inline формы"""
        form = super().get_form(request, obj, **kwargs)
        # Сохраняем объект для использования в inline
        self.obj = obj
        return form

    def save_formset(self, request, form, formset, change):
        """Автоматически устанавливаем valve_series для новых записей"""
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.valve_series_id and form.instance.pk:
                instance.valve_series = form.instance
                print(f"DEBUG: Set valve_series for new instance: {form.instance}")
            instance.save()
        formset.save_m2m()

    # attributes_count.short_description = _("Заполнено атрибутов")


@admin.register(ValveSeriesAttributeValue)
class ValveSeriesAttributeValueAdmin(admin.ModelAdmin) :
    list_display = ['valve_series' , 'attribute' , 'get_display_value' , 'is_predefined']
    list_filter = ['valve_series' , 'attribute']
    search_fields = ['valve_series__symbolic_code' , 'attribute__name' , 'custom_value']
    list_select_related = ('valve_series' , 'attribute' , 'predefined_value')

    def get_readonly_fields(self , request , obj=None) :
        """Для существующих объектов делаем атрибут readonly"""
        if obj :
            return ['attribute']
        return []

    def get_display_value(self , obj) :
        return obj.get_display_value()

    get_display_value.short_description = _("Значение")

    def is_predefined(self , obj) :
        return bool(obj.predefined_value)

    is_predefined.short_description = _("Из справочника")
    is_predefined.boolean = True

    def formfield_for_foreignkey(self , db_field , request , **kwargs) :
        """Ограничиваем выбор значений в зависимости от атрибута"""
        if db_field.name == "predefined_value" :
            # Получаем object_id из URL
            object_id = request.resolver_match.kwargs.get('object_id')
            if object_id :
                try :
                    obj = self.get_object(request , object_id)
                    if obj and obj.attribute_id :
                        kwargs["queryset"] = EAVValue.objects.filter(
                            attribute_id=obj.attribute_id ,
                            is_active=True
                        ).order_by('order' , 'display_name')
                except ValveSeriesAttributeValue.DoesNotExist :
                    pass
        return super().formfield_for_foreignkey(db_field , request , **kwargs)


# Дополнительные полезные админки
@admin.register(ValveVarietyAttribute)
class ValveVarietyAttributeAdmin(admin.ModelAdmin) :
    """Админка для связи разновидностей и атрибутов"""
    list_display = ['valve_variety' , 'attribute' , 'is_required' , 'order']
    list_filter = ['valve_variety' , 'is_required']
    list_editable = ['is_required' , 'order']
    autocomplete_fields = ['valve_variety' , 'attribute']
    list_select_related = ('valve_variety' , 'attribute')



class ValveSeriesDnPnTorqueMountDataAdmin(admin.ModelAdmin) :
    list_display = (
        'get_display_name' ,
        'valve_series_dn' ,
        'valve_series_max_pn_option' ,
        'valve_model_torque_to_open' ,
        'valve_model_torque_to_close' ,
        'valve_model_rotations_to_open' ,
        'valve_model_stem_size' ,
        'get_mounting_plates'
    )

    list_filter = (
        'valve_model_model_series' ,
        'valve_series_dn' ,
        'valve_series_max_pn_option' ,
        'valve_model_stem_size' ,
    )

    search_fields = (
        'valve_model_model_series__symbolic_code' ,
        'valve_series_dn__dn_value' ,
        'valve_series_max_pn_option__pn_value' ,
    )

    filter_horizontal = ('valve_model_mounting_plate' ,)

    fieldsets = (
        (_('Основная информация') , {
            'fields' : (
                'valve_model_model_series' ,
                ('valve_series_dn' , 'valve_series_max_pn_option') ,
            )
        }) ,
        (_('Технические характеристики') , {
            'fields' : (
                ('valve_model_torque_to_open' , 'valve_model_torque_to_close') ,
                'valve_model_rotations_to_open' ,
                'valve_model_stem_size' ,
            )
        }) ,
        (_('Монтажные характеристики') , {
            'fields' : (
                'valve_model_mounting_plate' ,
            )
        }) ,
    )

    def get_queryset(self , request) :
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'valve_model_model_series' ,
            'valve_series_dn' ,
            'valve_series_max_pn_option' ,
            'valve_model_stem_size'
        ).prefetch_related('valve_model_mounting_plate')

    def get_display_name(self , obj) :
        """Кастомное отображение названия записи"""
        if obj.valve_model_model_series :
            return f"{obj.valve_model_model_series.symbolic_code} DN{obj.valve_series_dn.dn_value if obj.valve_series_dn else '?'} PN{obj.valve_series_max_pn_option.pn_value if obj.valve_series_max_pn_option else '?'}"
        return _("Не указана серия")

    get_display_name.short_description = _('Модель арматуры')
    get_display_name.admin_order_field = 'valve_model_model_series'

    def get_mounting_plates(self , obj) :
        """Отображение монтажных площадок в списке"""
        plates = obj.valve_model_mounting_plate.all()
        if plates :
            return ", ".join([plate.symbolic_code for plate in plates])
        return _("Не указаны")

    get_mounting_plates.short_description = _('Монтажные площадки')

    # Добавляем действие копирования
    actions = [duplicate_selected_action]

    def duplicate_selected_action(self , request , queryset) :
        """Кастомное действие копирования для этой модели"""
        for obj in queryset :
            new_obj = ValveSeriesDnPnTorqueMountData()

            # Копируем поля ForeignKey
            new_obj.valve_model_model_series = obj.valve_model_model_series
            new_obj.valve_series_dn = obj.valve_series_dn
            new_obj.valve_series_max_pn_option = obj.valve_series_max_pn_option
            new_obj.valve_model_stem_size = obj.valve_model_stem_size

            # Копируем числовые поля
            new_obj.valve_model_torque_to_open = obj.valve_model_torque_to_open
            new_obj.valve_model_torque_to_close = obj.valve_model_torque_to_close
            new_obj.valve_model_rotations_to_open = obj.valve_model_rotations_to_open

            new_obj.save()

            # Копируем ManyToMany поле
            for mounting_plate in obj.valve_model_mounting_plate.all() :
                new_obj.valve_model_mounting_plate.add(mounting_plate)

        self.message_user(request , _("Выбранные записи успешно скопированы."))

    duplicate_selected_action.short_description = _("Копировать выбранные записи")


class ValveLineEAVChoiceValueInline(admin.TabularInline) :
    """Inline для значений выбора"""
    model = ValveLineEAVChoiceValue
    extra = 1
    fields = ['value' , 'display_name' , 'sorting_order' , 'is_active']


@admin.register(ValveLineEAVSection)
class ValveLineEAVSectionAdmin(admin.ModelAdmin) :
    list_display = ['name' , 'code' , 'sorting_order' , 'valve_varieties_count']
    list_filter = ['valve_varieties']
    list_editable = ['sorting_order']
    filter_horizontal = ['valve_varieties']

    def valve_varieties_count(self , obj) :
        return obj.valve_varieties.count()

    valve_varieties_count.short_description = _('Количество типов арматуры')


@admin.register(ValveLineEAVAttribute)
class ValveLineEAVAttributeAdmin(admin.ModelAdmin) :
    list_display = ['name' , 'code' , 'section' , 'value_type' , 'is_required' , 'sorting_order' , 'is_active']
    list_filter = ['section' , 'value_type' , 'is_required' , 'is_active']
    list_editable = ['sorting_order' , 'is_active']
    search_fields = ['name' , 'code' , 'description']
    inlines = [ValveLineEAVChoiceValueInline]


@admin.register(ValveLineEAVChoiceValue)
class ValveLineEAVChoiceValueAdmin(admin.ModelAdmin) :
    list_display = ['attribute' , 'value' , 'display_name' , 'sorting_order' , 'is_active']
    list_filter = ['attribute' , 'is_active']
    list_editable = ['sorting_order' , 'is_active']
    search_fields = ['value' , 'display_name' , 'attribute__name']


class ValveLineEAVValueInline(admin.TabularInline) :
    """Inline для значений атрибутов ValveLine"""
    model = ValveLineEAVValue
    extra = 1
    verbose_name = _("Атрибут")
    verbose_name_plural = _("Атрибуты")

    def formfield_for_foreignkey(self , db_field , request , obj=None , **kwargs) :
        """Ограничиваем выбор в зависимости от типа арматуры ValveLine"""
        if db_field.name == "attribute" and obj :
            # Получаем доступные атрибуты для типа арматуры этого ValveLine
            if obj.valve_variety :
                available_attributes = ValveLineEAVAttribute.objects.filter(
                    section__valve_varieties=obj.valve_variety ,
                    is_active=True
                )
                kwargs["queryset"] = available_attributes
        return super().formfield_for_foreignkey(db_field , request , obj , **kwargs)
