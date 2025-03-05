from django.contrib import admin
from .models import PowerSupplies, ExdOption, IpOption, BodyCoatingOption, BlinkerOption, SwitchesParameters, \
    EnvTempParameters, DigitalProtocolsSupportOption, ControlUnitInstalledOption, ActuatorGearboxOutputType, \
    ValveTypes, HandWheelInstalledOption, OperatingModeOption, ActuatorGearBoxCombinationTypes, MountingPlateTypes, \
    StemShapes, StemSize, ThreadTypes, MeasureUnits, ThreadSize, CertificateType, Certificate, \
    MechanicalIndicatorInstalledOption, SafetyPositionOption, ControlUnitTypeOption, ControlUnitLocationOption


class MountingPlateTypesAdmin(admin.ModelAdmin):
    ordering = ['symbolic_code']


class IpOptionAdmin(admin.ModelAdmin):
    ordering = ['ip_rank']
    list_display = ('symbolic_code', 'ip_rank', 'text_description')


class StemSizeAdmin(admin.ModelAdmin):
    # Показать важные поля в списке объектов модели
    ordering = ['stem_type', 'symbolic_code']
    list_display = ('symbolic_code', 'stem_type', 'stem_diameter', 'text_description')


admin.site.register(PowerSupplies)
admin.site.register(ExdOption)
admin.site.register(MechanicalIndicatorInstalledOption)
admin.site.register(IpOption, IpOptionAdmin)
admin.site.register(BodyCoatingOption)
admin.site.register(BlinkerOption)
admin.site.register(SwitchesParameters)
admin.site.register(EnvTempParameters)
admin.site.register(DigitalProtocolsSupportOption)
admin.site.register(ControlUnitInstalledOption)
admin.site.register(ActuatorGearboxOutputType)
admin.site.register(ValveTypes)
admin.site.register(HandWheelInstalledOption)
admin.site.register(OperatingModeOption)
admin.site.register(ActuatorGearBoxCombinationTypes)
admin.site.register(MountingPlateTypes, MountingPlateTypesAdmin)
admin.site.register(StemShapes)
admin.site.register(StemSize, StemSizeAdmin)
admin.site.register(ThreadTypes)
admin.site.register(MeasureUnits)
admin.site.register(ThreadSize)
admin.site.register(CertificateType)
admin.site.register(Certificate)
admin.site.register(SafetyPositionOption)
admin.site.register(ControlUnitTypeOption)
admin.site.register(ControlUnitLocationOption)
