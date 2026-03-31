from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django import forms
import json


from .models import PowerSupplies, ExdOption, IpOption, BodyCoatingOption, BlinkerOption, SwitchesParameters, \
    EnvTempParameters, DigitalProtocolsSupportOption, ControlUnitInstalledOption, ActuatorGearboxOutputType, \
    ValveTypes, HandWheelInstalledOption, OperatingModeOption, ActuatorGearBoxCombinationTypes, MountingPlateTypes, \
    StemShapes, StemSize, ThreadTypes, MeasureUnits, ThreadSize, CertVariety, CertData, \
    MechanicalIndicatorInstalledOption, SafetyPositionOption, ControlUnitTypeOption, ControlUnitLocationOption, \
    ClimaticConditions, ClimaticEquipmentPlacementClassifier, ClimaticZoneClassifier, PnVariety, DnVariety, \
    BodyColor, OptionVariety, ValveFunctionVariety, CoatingVariety, SealingClass, WarrantyTimePeriodVariety, \
    ValveActuationVariety, PneumaticAirSupplyPressure, PneumaticConnection, ThreadSizeSetItem, ThreadSizeSet, \
    ThreadInnerOuter


class MeasureUnitsAdmin(admin.ModelAdmin):
    list_display = (
    'id', 'name', 'code',  'description',  'sorting_order', 'is_active')
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    ordering = ['sorting_order']


class MountingPlateTypesAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'code',  'description', 'sorting_order', 'is_active')
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    ordering = ['sorting_order']


class IpOptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name',  'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    search_fields = ('name' , 'code' , 'description')  # ← ДОБАВЬТЕ
    ordering = ['sorting_order']


class StemSizeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'sorting_order',  'stem_type',
                    'stem_diameter')  # , 'description', 'description')
    list_editable = ['name', 'code', 'sorting_order']
    search_fields = ('name' , 'code' , 'description')  # ← ДОБАВЬТЕ
    ordering = ['sorting_order']


class OptionVarietyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'sorting_order', 'is_active']
    list_editable = ['sorting_order', 'is_active']
    list_filter = ['is_active']
    ordering = ['sorting_order']


class ValveFunctionVarietyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'description_preview', 'sorting_order', 'is_active']
    list_editable = ['sorting_order', 'is_active']
    search_fields = ['name', 'code', 'description']
    list_filter = ['is_active']
    ordering = ['sorting_order']

    # Убираем ненужные методы, так как нет ManyToManyField
    # Вместо display_valve_function_varieties используем description_preview

    def description_preview(self, obj):
        """Превью описания (первые 50 символов)"""
        return obj.description[:50] + "..." if len(obj.description) > 50 else obj.description

    description_preview.short_description = _('Описание (превью)')

    # Опционально: настройки для формы редактирования
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'sorting_order', 'is_active')
        }),
        (_('Описание'), {
            'fields': ('description',),
            'classes': ('collapse',)  # Сворачиваемый блок
        }),
    )

    def display_related_valve_lines(self, obj):
        """Отображает связанные серии арматуры"""
        return ", ".join([line.symbolic_code for line in obj.valve_line_valve_function.all()[:5]])  # первые 5

    display_related_valve_lines.short_description = _('Связанные серии арматуры')


class SealingClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'sorting_order', 'is_active']
    list_editable = ['sorting_order', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['sorting_order']


class ValveActuationVarietyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'sorting_order', 'is_active']
    list_editable = ['sorting_order', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['sorting_order']


class BodyColorAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'ral_code', 'hex_code', 'sorting_order', 'is_active', 'color_preview']
    list_editable = ['sorting_order', 'is_active']
    search_fields = ['name', 'code', 'ral_code']
    ordering = ['sorting_order']

    def color_preview(self, obj):
        if obj.hex_code:
            return format_html(
                '<div style="width: 30px; height: 20px; background-color: {}; border: 1px solid #ccc;"></div>',
                obj.hex_code
            )
        return "-"

    color_preview.short_description = _("Предпросмотр")


class CoatingVarietyAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'sorting_order', 'is_active']
    list_editable = ['sorting_order', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['sorting_order']


class DnVarietyAdmin(admin.ModelAdmin):
    list_display = (
    'id', 'name', 'code', 'sorting_order', 'diameter_metric', 'diameter_inches')  # , 'description', 'description')
    list_editable = ['name', 'code', 'sorting_order']
    search_fields = ['id', 'name']  # Укажите поля для поиска
    ordering = ['sorting_order']

class PnVarietyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'sorting_order',)  # , 'description', 'description')
    list_editable = ['name', 'code', 'sorting_order']
    search_fields = ['id', 'name']  # Укажите поля для поиска
    ordering = ['sorting_order']

class PowerSuppliesAdmin(admin.ModelAdmin):
    list_display = ['id', 'name',  'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    ordering = ['sorting_order']


class ExdOptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name',  'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order']
    search_fields = ('name' , 'code' , 'description')  # ← ДОБАВЬТЕ
    ordering = ['sorting_order']

class MechanicalIndicatorInstalledOptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name',  'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    ordering = ['sorting_order']

class BodyCoatingOptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    search_fields = ('name' , 'code' , 'description')  # ← ДОБАВЬТЕ
    ordering = ['sorting_order']

class BlinkerOptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name',  'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    ordering = ['sorting_order']

class SwitchesParametersAdmin(admin.ModelAdmin):
    list_display = ['id', 'name',  'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    ordering = ['sorting_order']

class EnvTempParametersAdmin(admin.ModelAdmin):
    list_display = ['id', 'name',  'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    search_fields = ('name' , 'code' , 'description')  # ← ДОБАВЬТЕ
    ordering = ['sorting_order']

class DigitalProtocolsSupportOptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']


class ControlUnitInstalledOptionForm(forms.ModelForm):
    """Форма для редактирования JSON поля"""

    feature_list_display = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 10,
            'class': 'vLargeTextField json-editor',
            'style': 'font-family: monospace;'
        }),
        label="Параметры блока управления",
        help_text="Редактируйте JSON напрямую или используйте таблицу ниже"
    )

    class Meta:
        model = ControlUnitInstalledOption
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Преобразуем JSON в отформатированную строку для отображения
        if self.instance and self.instance.feature_list:
            try:
                self.fields['feature_list_display'].initial = json.dumps(
                    self.instance.feature_list,
                    ensure_ascii=False,
                    indent=2
                )
            except:
                self.fields['feature_list_display'].initial = json.dumps(
                    [],
                    ensure_ascii=False,
                    indent=2
                )
        else:
            self.fields['feature_list_display'].initial = json.dumps(
                [],
                ensure_ascii=False,
                indent=2
            )

    def clean(self):
        cleaned_data = super().clean()

        # Парсим JSON из текстового поля
        json_str = cleaned_data.get('feature_list_display', '[]')
        if json_str:
            try:
                parsed_json = json.loads(json_str)
                # Валидация структуры
                if not isinstance(parsed_json, list):
                    raise forms.ValidationError("Должен быть массив (список)")

                for item in parsed_json:
                    if not isinstance(item, dict):
                        raise forms.ValidationError("Каждый элемент должен быть объектом")
                    if 'value' not in item:
                        raise forms.ValidationError("У каждого элемента должно быть поле 'value'")

                cleaned_data['feature_list'] = parsed_json
            except json.JSONDecodeError as e:
                raise forms.ValidationError(f"Ошибка в JSON: {e}")
        else:
            cleaned_data['feature_list'] = []

        return cleaned_data

    def save(self, commit=True):
        """Сохраняем форму, включая JSON поле"""
        instance = super().save(commit=False)

        # Убеждаемся, что feature_list установлен из cleaned_data
        if 'feature_list' in self.cleaned_data:
            instance.feature_list = self.cleaned_data['feature_list']

        if commit:
            instance.save()
            self.save_m2m()  # для ManyToMany полей если есть

        return instance


@admin.register(ControlUnitInstalledOption)
class ControlUnitInstalledOptionAdmin(admin.ModelAdmin):
    form = ControlUnitInstalledOptionForm

    list_display = ['name', 'code', 'encoding', 'sorting_order', 'is_active']
    list_editable = ['code', 'encoding', 'sorting_order', 'is_active']
    list_filter = ['is_active', 'encoding']
    search_fields = ['name', 'code', 'encoding']
    ordering = ['sorting_order']

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'code', 'encoding', 'description')
        }),
        ('Параметры блока управления', {
            'fields': ('feature_list_display',),
            'description': '''
                <div style="background: #f8f9fa; padding: 10px; margin: 10px 0;">
                    <strong>Формат JSON:</strong>
                    <pre style="background: #fff; padding: 10px; border: 1px solid #ddd;">
[
  {"display_name": "Питание от питания привода", "value": "нет"},
  {"display_name": "Питание отдельное", "value": "да"},
  {"display_name": "Селектор Местное/Удаленное", "value": "нет"}
]
                    </pre>
                </div>
            ''',
        }),
        ('Настройки', {
            'fields': ('sorting_order', 'is_active')
        }),
    )
    class Media:
        css = {
            'all': ('admin/css/json-editor.css',)
        }
        js = ('admin/js/json-editor.js',)

class ActuatorGearboxOutputTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name',  'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    search_fields = ('name' , 'code' , 'description')  # ← ДОБАВЬТЕ
    ordering = ['sorting_order']

class ValveTypesAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    ordering = ['sorting_order']

class HandWheelInstalledOptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name',  'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    search_fields = ('name' , 'code' , 'description')  # ← ДОБАВЬТЕ
    ordering = ['sorting_order']

class OperatingModeOptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    ordering = ['sorting_order']

class ActuatorGearBoxCombinationTypesAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    ordering = ['sorting_order']

class StemShapesAdmin(admin.ModelAdmin):
    list_display = ['id', 'name',  'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    search_fields = ('name' , 'code' , 'description')  # ← ДОБАВЬТЕ
    ordering = ['sorting_order']

class ThreadTypesAdmin(admin.ModelAdmin):
    list_display = ['id', 'name',  'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    ordering = ['sorting_order']

class ThreadSizeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name',  'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    ordering = ['sorting_order']

class SafetyPositionOptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    ordering = ['sorting_order']

class ControlUnitTypeOptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    ordering = ['sorting_order']

class ControlUnitLocationOptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    ordering = ['sorting_order']

class ClimaticZoneClassifierAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']


class ClimaticEquipmentPlacementClassifierAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code', 'sorting_order', 'description']
    list_editable = ['name', 'code', 'sorting_order']
    ordering = ['sorting_order']

class ClimaticConditionsAdmin(admin.ModelAdmin):
    list_display = ['id', 'name',  'code', 'sorting_order', 'description']
    list_editable = ['name', 'code', 'sorting_order']
    ordering = ['sorting_order']


@admin.register(PneumaticAirSupplyPressure)
class PneumaticAirSupplyPressureAdmin(admin.ModelAdmin) :
    """Админка для давления питания пневмопривода"""

    list_display = ('name' , 'code' , 'pressure_bar' , 'sorting_order' , 'is_active')
    list_editable = ('sorting_order' , 'is_active')
    list_filter = ('is_active' ,)
    search_fields = ('name' , 'code' , 'description')
    ordering = ('sorting_order' ,)

    fieldsets = (
        (_('Основная информация') , {
            'fields' : ('name' , 'code' , 'pressure_bar' , 'description')
        }) ,
        (_('Настройки') , {
            'fields' : ('sorting_order' , 'is_active')
        }) ,
    )

    def get_pressure_display(self , obj) :
        """Отображает давление в различных единицах"""
        return f"{obj.get_pressure_display('bar')} | {obj.get_pressure_display('mpa')}"

    get_pressure_display.short_description = _('Давление в различных единицах')

    readonly_fields = ('get_pressure_display' ,)


# Inline для элементов набора
class ThreadSizeSetItemInline(admin.TabularInline):
    model = ThreadSizeSetItem
    extra = 1  # Показывать 1 пустую форму
    max_num = 50  # Максимальное количество элементов
    ordering = ['position']

    fields = ['position', 'thread_size', 'thread_size_display']
    readonly_fields = ['thread_size_display']

    def thread_size_display(self, obj):
        """Отображение названия резьбы с количеством"""
        if obj.thread_size:
            # Предполагаем, что в ThreadSize.name уже хранится "2xNPT 1/2"
            return obj.thread_size.name
        return "-"

    thread_size_display.short_description = "Название (с количеством)"


@admin.register(ThreadSizeSet)
class ThreadSizeSetAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'items_count_preview',
        'thread_sizes_list', 'sorting_order', 'is_active'
    ]

    list_filter = ['is_active']
    search_fields = ['name', 'code', 'description']

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'code', 'description')
        }),
        ('Настройки', {
            'fields': ('sorting_order', 'is_active')
        }),
    )

    inlines = [ThreadSizeSetItemInline]

    def items_count_preview(self, obj):
        """Количество элементов в наборе"""
        count = obj.thread_items.count()
        return format_html(
            '<span class="badge" style="background: #4CAF50; color: white; padding: 2px 8px; border-radius: 10px;">'
            '{} шт.</span>',
            count
        )

    items_count_preview.short_description = "Кол-во"

    def thread_sizes_list(self, obj):
        """Список всех резьб в наборе"""
        items = obj.get_thread_items()
        if items.exists():
            item_list = []
            for item in items:
                if item.thread_size:
                    item_list.append(item.thread_size.name)
                else:
                    item_list.append("Не указано")

            # Показываем только первые 5 элементов
            preview = ", ".join(item_list[:5])
            if len(item_list) > 5:
                preview += f" ... (+{len(item_list) - 5})"

            return preview
        return "-"

    thread_sizes_list.short_description = "Резьбы в наборе"

    class Media:
        css = {
            'all': ('admin/css/thread_size_set.css',)
        }


@admin.register(ThreadSizeSetItem)
class ThreadSizeSetItemAdmin(admin.ModelAdmin):
    list_display = [
        'thread_set', 'position', 'thread_size_display'
    ]

    list_filter = ['thread_set']
    search_fields = ['thread_set__name', 'thread_size__name']

    def thread_size_display(self, obj):
        """Отображение названия резьбы с количеством"""
        if obj.thread_size:
            return obj.thread_size.name
        return "-"

    thread_size_display.short_description = "Резьба (с количеством)"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'thread_set', 'thread_size'
        )
admin.site.register(PowerSupplies, PowerSuppliesAdmin)
admin.site.register(ExdOption, ExdOptionAdmin)
admin.site.register(MechanicalIndicatorInstalledOption, MechanicalIndicatorInstalledOptionAdmin)
admin.site.register(IpOption, IpOptionAdmin)
admin.site.register(BodyCoatingOption, BodyCoatingOptionAdmin)
admin.site.register(BlinkerOption, BlinkerOptionAdmin)
admin.site.register(SwitchesParameters, SwitchesParametersAdmin)
admin.site.register(EnvTempParameters, EnvTempParametersAdmin)
admin.site.register(DigitalProtocolsSupportOption, DigitalProtocolsSupportOptionAdmin)
# admin.site.register(ControlUnitInstalledOption, ControlUnitInstalledOptionAdmin)
admin.site.register(ActuatorGearboxOutputType, ActuatorGearboxOutputTypeAdmin)
admin.site.register(ValveTypes, ValveTypesAdmin)
admin.site.register(HandWheelInstalledOption, HandWheelInstalledOptionAdmin)
admin.site.register(OperatingModeOption, OperatingModeOptionAdmin)
admin.site.register(ActuatorGearBoxCombinationTypes, ActuatorGearBoxCombinationTypesAdmin)
admin.site.register(MountingPlateTypes, MountingPlateTypesAdmin)
admin.site.register(StemShapes, StemShapesAdmin)
admin.site.register(StemSize, StemSizeAdmin)

admin.site.register(ThreadTypes, ThreadTypesAdmin)
admin.site.register(MeasureUnits, MeasureUnitsAdmin)
admin.site.register(ThreadSize, ThreadSizeAdmin)
admin.site.register(CertVariety)
admin.site.register(CertData)
admin.site.register(SafetyPositionOption, SafetyPositionOptionAdmin)
admin.site.register(ControlUnitTypeOption, ControlUnitTypeOptionAdmin)
admin.site.register(ControlUnitLocationOption, ControlUnitLocationOptionAdmin)
admin.site.register(ClimaticZoneClassifier, ClimaticZoneClassifierAdmin)
admin.site.register(ClimaticEquipmentPlacementClassifier, ClimaticEquipmentPlacementClassifierAdmin)
admin.site.register(ClimaticConditions, ClimaticConditionsAdmin)
admin.site.register(DnVariety, DnVarietyAdmin)
admin.site.register(PnVariety, PnVarietyAdmin)
admin.site.register(BodyColor, BodyColorAdmin)
admin.site.register(OptionVariety, OptionVarietyAdmin)
admin.site.register(ValveFunctionVariety, ValveFunctionVarietyAdmin)
admin.site.register(CoatingVariety, CoatingVarietyAdmin)
admin.site.register(WarrantyTimePeriodVariety)
admin.site.register(SealingClass, SealingClassAdmin)
admin.site.register(ValveActuationVariety, ValveActuationVarietyAdmin)
admin.site.register(PneumaticConnection)
admin.site.register(ThreadInnerOuter)
