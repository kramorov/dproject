import graphene
from graphene_django import DjangoObjectType
from django.contrib.contenttypes.models import ContentType

from params.models import (
    PowerSupplies , ControlUnitLocationOption , ControlUnitTypeOption , SafetyPositionOption ,
    ExdOption , IpOption , BodyCoatingOption , BlinkerOption , SwitchesParameters , EnvTempParameters ,
    ClimaticZoneClassifier , ClimaticEquipmentPlacementClassifier , ClimaticConditions ,
    DigitalProtocolsSupportOption , MechanicalIndicatorInstalledOption , ControlUnitInstalledOption ,
    ActuatorGearboxOutputType , ActuatorGearBoxCombinationTypes , ValveTypes , HandWheelInstalledOption ,
    OperatingModeOption , MountingPlateTypes , StemShapes , StemSize , ThreadTypes , MeasureUnits ,
    ThreadSize , CertVariety , CertData , DnVariety , PnVariety , OptionVariety , BodyColor ,
    ValveFunctionVariety , ValveActuationVariety , SealingClass , CoatingVariety , WarrantyTimePeriodVariety
)


class PowerSuppliesNode(DjangoObjectType) :
    voltage_type_display = graphene.String()

    class Meta :
        model = PowerSupplies
        fields = (
        'id' , 'name' , 'code' , 'voltage_value' , 'voltage_type' , 'description' , 'sorting_order' , 'is_active')

    def resolve_voltage_type_display(self , info) :
        return self.get_voltage_type_display()


class ControlUnitLocationOptionNode(DjangoObjectType) :
    class Meta :
        model = ControlUnitLocationOption
        fields = ('id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active')


class ControlUnitTypeOptionNode(DjangoObjectType) :
    class Meta :
        model = ControlUnitTypeOption
        fields = ('id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active')


class SafetyPositionOptionNode(DjangoObjectType) :
    class Meta :
        model = SafetyPositionOption
        fields = ('id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active')


class ExdOptionNode(DjangoObjectType) :
    class Meta :
        model = ExdOption
        fields = ('id' , 'name' , 'code' , 'exd_full_code' , 'description' , 'sorting_order' , 'is_active')


class IpOptionNode(DjangoObjectType) :
    class Meta :
        model = IpOption
        fields = ('id' , 'name' , 'code' , 'ip_rank' , 'description' , 'sorting_order' , 'is_active')


class BodyCoatingOptionNode(DjangoObjectType) :
    class Meta :
        model = BodyCoatingOption
        fields = ('id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active')


class BlinkerOptionNode(DjangoObjectType) :
    class Meta :
        model = BlinkerOption
        fields = ('id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active')


class SwitchesParametersNode(DjangoObjectType) :
    class Meta :
        model = SwitchesParameters
        fields = ('id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active')


class EnvTempParametersNode(DjangoObjectType) :
    class Meta :
        model = EnvTempParameters
        fields = ('id' , 'name' , 'code' , 'min_temp' , 'max_temp' , 'description' , 'sorting_order' , 'is_active')


class ClimaticZoneClassifierNode(DjangoObjectType) :
    class Meta :
        model = ClimaticZoneClassifier
        fields = ('id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active')


class ClimaticEquipmentPlacementClassifierNode(DjangoObjectType) :
    class Meta :
        model = ClimaticEquipmentPlacementClassifier
        fields = ('id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active')


class ClimaticConditionsNode(DjangoObjectType) :
    class Meta :
        model = ClimaticConditions
        fields = (
            'id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active' ,
            'climaticZone' , 'climaticPlacement' , 'min_temp_work' , 'max_temp_work' ,
            'min_temp_extremal' , 'max_temp_extremal'
        )


class DigitalProtocolsSupportOptionNode(DjangoObjectType) :
    class Meta :
        model = DigitalProtocolsSupportOption
        fields = ('id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active')


class MechanicalIndicatorInstalledOptionNode(DjangoObjectType) :
    class Meta :
        model = MechanicalIndicatorInstalledOption
        fields = ('id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active')


class ControlUnitInstalledOptionNode(DjangoObjectType) :
    class Meta :
        model = ControlUnitInstalledOption
        fields = ('id' , 'name' , 'code' , 'encoding' , 'description' , 'sorting_order' , 'is_active')


class ActuatorGearboxOutputTypeNode(DjangoObjectType) :
    class Meta :
        model = ActuatorGearboxOutputType
        fields = ('id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active')


class ActuatorGearBoxCombinationTypesNode(DjangoObjectType) :
    class Meta :
        model = ActuatorGearBoxCombinationTypes
        fields = (
            'id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active' ,
            'electric_actuator_type' , 'gearbox_type' , 'pneumatic_actuator_type'
        )


class ValveTypesNode(DjangoObjectType) :
    class Meta :
        model = ValveTypes
        fields = (
        'id' , 'name' , 'code' , 'actuator_gearbox_combinations' , 'description' , 'sorting_order' , 'is_active')


class HandWheelInstalledOptionNode(DjangoObjectType) :
    class Meta :
        model = HandWheelInstalledOption
        fields = ('id' , 'name' , 'code' , 'encoding' , 'description' , 'sorting_order' , 'is_active')


class OperatingModeOptionNode(DjangoObjectType) :
    class Meta :
        model = OperatingModeOption
        fields = ('id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active')


class MountingPlateTypesNode(DjangoObjectType) :
    class Meta :
        model = MountingPlateTypes
        fields = ('id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active')


class StemShapesNode(DjangoObjectType) :
    class Meta :
        model = StemShapes
        fields = ('id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active')


class StemSizeNode(DjangoObjectType) :
    class Meta :
        model = StemSize
        fields = (
            'id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active' ,
            'stem_type' , 'stem_diameter' , 'chunk_x' , 'chunk_y' , 'chunk_z' , 'thread_pitch'
        )


class ThreadTypesNode(DjangoObjectType) :
    class Meta :
        model = ThreadTypes
        fields = ('id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active')


class MeasureUnitsNode(DjangoObjectType) :
    measure_type_display = graphene.String()

    class Meta :
        model = MeasureUnits
        fields = ('id' , 'name' , 'code' , 'measure_type' , 'description' , 'sorting_order' , 'is_active')

    def resolve_measure_type_display(self , info) :
        return self.get_measure_type_display()


class ThreadSizeNode(DjangoObjectType) :
    class Meta :
        model = ThreadSize
        fields = (
            'id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active' ,
            'thread_type' , 'thread_diameter' , 'thread_pitch' , 'measure_units'
        )


class CertVarietyNode(DjangoObjectType) :
    class Meta :
        model = CertVariety
        fields = ('id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active')


class CertDataNode(DjangoObjectType) :
    class Meta :
        model = CertData
        fields = (
            'id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active' ,
            'cert_variety' , 'valid_from' , 'valid_until'
        )


class DnVarietyNode(DjangoObjectType) :
    class Meta :
        model = DnVariety
        fields = (
            'id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active' ,
            'diameter_metric' , 'diameter_inches'
        )


class PnVarietyNode(DjangoObjectType) :
    class Meta :
        model = PnVariety
        fields = (
            'id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active' ,
            'pressure_bar'
        )


class OptionVarietyNode(DjangoObjectType) :
    class Meta :
        model = OptionVariety
        fields = ('id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active')


class BodyColorNode(DjangoObjectType) :
    color_display = graphene.String()

    class Meta :
        model = BodyColor
        fields = (
            'id' , 'name' , 'code' , 'description' , 'hex_code' , 'ral_code' ,
            'sorting_order' , 'is_active'
        )

    def resolve_color_display(self , info) :
        return self.get_color_display()


class ValveFunctionVarietyNode(DjangoObjectType) :
    class Meta :
        model = ValveFunctionVariety
        fields = ('id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active')


class ValveActuationVarietyNode(DjangoObjectType) :
    class Meta :
        model = ValveActuationVariety
        fields = ('id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active')


class SealingClassNode(DjangoObjectType) :
    class Meta :
        model = SealingClass
        fields = (
            'id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active' ,
            'valve_function_variety'
        )


class CoatingVarietyNode(DjangoObjectType) :
    class Meta :
        model = CoatingVariety
        fields = (
            'id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active' ,
            'thickness'
        )


class WarrantyTimePeriodVarietyNode(DjangoObjectType) :
    class Meta :
        model = WarrantyTimePeriodVariety
        fields = ('id' , 'name' , 'code' , 'description' , 'sorting_order' , 'is_active')