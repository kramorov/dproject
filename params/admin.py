from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import PowerSupplies , ExdOption , IpOption , BodyCoatingOption , BlinkerOption , SwitchesParameters , \
    EnvTempParameters , DigitalProtocolsSupportOption , ControlUnitInstalledOption , ActuatorGearboxOutputType , \
    ValveTypes , HandWheelInstalledOption , OperatingModeOption , ActuatorGearBoxCombinationTypes , MountingPlateTypes , \
    StemShapes , StemSize , ThreadTypes , MeasureUnits , ThreadSize , CertVariety , CertData , \
    MechanicalIndicatorInstalledOption , SafetyPositionOption , ControlUnitTypeOption , ControlUnitLocationOption , \
    ClimaticConditions , ClimaticEquipmentPlacementClassifier , ClimaticZoneClassifier , PnVariety , DnVariety , \
    BodyColor , OptionVariety , ValveFunctionVariety , CoatingVariety , SealingClass , WarrantyTimePeriodVariety , \
    ValveActuationVariety , PneumaticAirSupplyPressure , PneumaticConnection


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


class ControlUnitInstalledOptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name',  'code', 'sorting_order', 'is_active']
    list_editable = ['name', 'code', 'sorting_order', 'is_active']
    ordering = ['sorting_order']

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


admin.site.register(PowerSupplies, PowerSuppliesAdmin)
admin.site.register(ExdOption, ExdOptionAdmin)
admin.site.register(MechanicalIndicatorInstalledOption, MechanicalIndicatorInstalledOptionAdmin)
admin.site.register(IpOption, IpOptionAdmin)
admin.site.register(BodyCoatingOption, BodyCoatingOptionAdmin)
admin.site.register(BlinkerOption, BlinkerOptionAdmin)
admin.site.register(SwitchesParameters, SwitchesParametersAdmin)
admin.site.register(EnvTempParameters, EnvTempParametersAdmin)
admin.site.register(DigitalProtocolsSupportOption, DigitalProtocolsSupportOptionAdmin)
admin.site.register(ControlUnitInstalledOption, ControlUnitInstalledOptionAdmin)
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
