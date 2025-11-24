# params/query.py

import graphene
from graphene_django import DjangoObjectType

from params.graphql.types import (
    PowerSuppliesNode, ControlUnitLocationOptionNode, ControlUnitTypeOptionNode,
    SafetyPositionOptionNode, ExdOptionNode, IpOptionNode, BodyCoatingOptionNode,
    BlinkerOptionNode, SwitchesParametersNode, EnvTempParametersNode,
    DigitalProtocolsSupportOptionNode, MechanicalIndicatorInstalledOptionNode,
    ControlUnitInstalledOptionNode, ActuatorGearboxOutputTypeNode,
    ActuatorGearBoxCombinationTypesNode, ValveTypesNode, HandWheelInstalledOptionNode,
    OperatingModeOptionNode, MountingPlateTypesNode, StemShapesNode, StemSizeNode,
    ThreadTypesNode, MeasureUnitsNode, ThreadSizeNode, ClimaticConditionsNode,
    ClimaticEquipmentPlacementClassifierNode, ClimaticZoneClassifierNode,
    CertDataNode, CertVarietyNode, DnVarietyNode, PnVarietyNode, OptionVarietyNode,
    BodyColorNode, ValveFunctionVarietyNode, ValveActuationVarietyNode,
    SealingClassNode, CoatingVarietyNode, WarrantyTimePeriodVarietyNode
)

from params.models import (
    PowerSupplies, ControlUnitLocationOption, ControlUnitTypeOption, SafetyPositionOption,
    ExdOption, IpOption, BodyCoatingOption, BlinkerOption, SwitchesParameters, EnvTempParameters,
    DigitalProtocolsSupportOption, MechanicalIndicatorInstalledOption, ControlUnitInstalledOption,
    ActuatorGearboxOutputType, ActuatorGearBoxCombinationTypes, ValveTypes, HandWheelInstalledOption,
    OperatingModeOption, MountingPlateTypes, StemShapes, StemSize, ThreadTypes, MeasureUnits, ThreadSize,
    ClimaticZoneClassifier, ClimaticEquipmentPlacementClassifier, ClimaticConditions,
    CertData, CertVariety, DnVariety, PnVariety, OptionVariety, BodyColor,
    ValveFunctionVariety, ValveActuationVariety, SealingClass, CoatingVariety, WarrantyTimePeriodVariety
)


class Query(graphene.ObjectType):
    # PowerSupplies
    params_power_supplies = graphene.List(
        PowerSuppliesNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        voltage_value=graphene.Int(),
        voltage_type=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_power_supplies(self, info, **kwargs):
        queryset = PowerSupplies.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('voltage_value'):
            queryset = queryset.filter(voltage_value=kwargs['voltage_value'])
        if kwargs.get('voltage_type'):
            queryset = queryset.filter(voltage_type__icontains=kwargs['voltage_type'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # ControlUnitLocationOption
    params_control_unit_location_options = graphene.List(
        ControlUnitLocationOptionNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_control_unit_location_options(self, info, **kwargs):
        queryset = ControlUnitLocationOption.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # ControlUnitTypeOption
    params_control_unit_type_options = graphene.List(
        ControlUnitTypeOptionNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_control_unit_type_options(self, info, **kwargs):
        queryset = ControlUnitTypeOption.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # SafetyPositionOption
    params_safety_position_options = graphene.List(
        SafetyPositionOptionNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_safety_position_options(self, info, **kwargs):
        queryset = SafetyPositionOption.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # ExdOption
    params_exd_options = graphene.List(
        ExdOptionNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        exd_full_code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_exd_options(self, info, **kwargs):
        queryset = ExdOption.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('exd_full_code'):
            queryset = queryset.filter(exd_full_code__icontains=kwargs['exd_full_code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # IpOption
    params_ip_options = graphene.List(
        IpOptionNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        ip_rank=graphene.Int(),
        is_active=graphene.Boolean()
    )

    def resolve_params_ip_options(self, info, **kwargs):
        queryset = IpOption.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('ip_rank'):
            queryset = queryset.filter(ip_rank=kwargs['ip_rank'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # BodyCoatingOption
    params_body_coating_options = graphene.List(
        BodyCoatingOptionNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_body_coating_options(self, info, **kwargs):
        queryset = BodyCoatingOption.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # BlinkerOption
    params_blinker_options = graphene.List(
        BlinkerOptionNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_blinker_options(self, info, **kwargs):
        queryset = BlinkerOption.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # SwitchesParameters
    params_switches_parameters = graphene.List(
        SwitchesParametersNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_switches_parameters(self, info, **kwargs):
        queryset = SwitchesParameters.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # EnvTempParameters
    params_env_temp_parameters = graphene.List(
        EnvTempParametersNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        min_temp=graphene.Int(),
        max_temp=graphene.Int(),
        is_active=graphene.Boolean()
    )

    def resolve_params_env_temp_parameters(self, info, **kwargs):
        queryset = EnvTempParameters.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('min_temp'):
            queryset = queryset.filter(min_temp__lte=kwargs['min_temp'])
        if kwargs.get('max_temp'):
            queryset = queryset.filter(max_temp__gte=kwargs['max_temp'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # DigitalProtocolsSupportOption
    params_digital_protocols_support_options = graphene.List(
        DigitalProtocolsSupportOptionNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_digital_protocols_support_options(self, info, **kwargs):
        queryset = DigitalProtocolsSupportOption.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # MechanicalIndicatorInstalledOption
    params_mechanical_indicator_installed_options = graphene.List(
        MechanicalIndicatorInstalledOptionNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_mechanical_indicator_installed_options(self, info, **kwargs):
        queryset = MechanicalIndicatorInstalledOption.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # ControlUnitInstalledOption
    params_control_unit_installed_options = graphene.List(
        ControlUnitInstalledOptionNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        encoding=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_control_unit_installed_options(self, info, **kwargs):
        queryset = ControlUnitInstalledOption.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('encoding'):
            queryset = queryset.filter(encoding__icontains=kwargs['encoding'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # ActuatorGearboxOutputType
    params_actuator_gearbox_output_types = graphene.List(
        ActuatorGearboxOutputTypeNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_actuator_gearbox_output_types(self, info, **kwargs):
        queryset = ActuatorGearboxOutputType.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # ActuatorGearBoxCombinationTypes
    params_actuator_gear_box_combination_types = graphene.List(
        ActuatorGearBoxCombinationTypesNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        electric_actuator_type=graphene.String(),
        gearbox_type=graphene.String(),
        pneumatic_actuator_type=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_actuator_gear_box_combination_types(self, info, **kwargs):
        queryset = ActuatorGearBoxCombinationTypes.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('electric_actuator_type'):
            queryset = queryset.filter(electric_actuator_type__icontains=kwargs['electric_actuator_type'])
        if kwargs.get('gearbox_type'):
            queryset = queryset.filter(gearbox_type__icontains=kwargs['gearbox_type'])
        if kwargs.get('pneumatic_actuator_type'):
            queryset = queryset.filter(pneumatic_actuator_type__icontains=kwargs['pneumatic_actuator_type'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # ValveTypes
    params_valve_types = graphene.List(
        ValveTypesNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        actuator_gearbox_combinations=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_valve_types(self, info, **kwargs):
        queryset = ValveTypes.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('actuator_gearbox_combinations'):
            queryset = queryset.filter(
                actuator_gearbox_combinations__icontains=kwargs['actuator_gearbox_combinations'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # HandWheelInstalledOption
    params_hand_wheel_installed_options = graphene.List(
        HandWheelInstalledOptionNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        encoding=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_hand_wheel_installed_options(self, info, **kwargs):
        queryset = HandWheelInstalledOption.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('encoding'):
            queryset = queryset.filter(encoding__icontains=kwargs['encoding'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # OperatingModeOption
    params_operating_mode_options = graphene.List(
        OperatingModeOptionNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_operating_mode_options(self, info, **kwargs):
        queryset = OperatingModeOption.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # MountingPlateTypes
    params_mounting_plate_types = graphene.List(
        MountingPlateTypesNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_mounting_plate_types(self, info, **kwargs):
        queryset = MountingPlateTypes.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # StemShapes
    params_stem_shapes = graphene.List(
        StemShapesNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_stem_shapes(self, info, **kwargs):
        queryset = StemShapes.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # StemSize
    params_stem_sizes = graphene.List(
        StemSizeNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        stem_type=graphene.ID(),
        stem_diameter=graphene.Float(),
        thread_pitch=graphene.Float(),
        is_active=graphene.Boolean()
    )

    def resolve_params_stem_sizes(self, info, **kwargs):
        queryset = StemSize.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('stem_type'):
            queryset = queryset.filter(stem_type=kwargs['stem_type'])
        if kwargs.get('stem_diameter'):
            queryset = queryset.filter(stem_diameter=kwargs['stem_diameter'])
        if kwargs.get('thread_pitch'):
            queryset = queryset.filter(thread_pitch=kwargs['thread_pitch'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # ThreadTypes
    params_thread_types = graphene.List(
        ThreadTypesNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_thread_types(self, info, **kwargs):
        queryset = ThreadTypes.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # MeasureUnits
    params_measure_units = graphene.List(
        MeasureUnitsNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        measure_type=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_measure_units(self, info, **kwargs):
        queryset = MeasureUnits.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('measure_type'):
            queryset = queryset.filter(measure_type__icontains=kwargs['measure_type'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('measure_type', 'sorting_order')

    # ThreadSize
    params_thread_sizes = graphene.List(
        ThreadSizeNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        thread_type=graphene.ID(),
        thread_diameter=graphene.Float(),
        thread_pitch=graphene.Float(),
        is_active=graphene.Boolean()
    )

    def resolve_params_thread_sizes(self, info, **kwargs):
        queryset = ThreadSize.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('thread_type'):
            queryset = queryset.filter(thread_type=kwargs['thread_type'])
        if kwargs.get('thread_diameter'):
            queryset = queryset.filter(thread_diameter=kwargs['thread_diameter'])
        if kwargs.get('thread_pitch'):
            queryset = queryset.filter(thread_pitch=kwargs['thread_pitch'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # ClimaticZoneClassifier
    params_climatic_zones = graphene.List(
        ClimaticZoneClassifierNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_climatic_zones(self, info, **kwargs):
        queryset = ClimaticZoneClassifier.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # ClimaticEquipmentPlacementClassifier
    params_climatic_placements = graphene.List(
        ClimaticEquipmentPlacementClassifierNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_climatic_placements(self, info, **kwargs):
        queryset = ClimaticEquipmentPlacementClassifier.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # ClimaticConditions
    params_climatic_conditions = graphene.List(
        ClimaticConditionsNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        climatic_zone=graphene.ID(),
        climatic_placement=graphene.ID(),
        is_active=graphene.Boolean()
    )

    def resolve_params_climatic_conditions(self, info, **kwargs):
        queryset = ClimaticConditions.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('climatic_zone'):
            queryset = queryset.filter(climaticZone_id=kwargs['climatic_zone'])
        if kwargs.get('climatic_placement'):
            queryset = queryset.filter(climaticPlacement_id=kwargs['climatic_placement'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # CertVariety
    params_cert_varieties = graphene.List(
        CertVarietyNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_cert_varieties(self, info, **kwargs):
        queryset = CertVariety.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # CertData
    params_cert_data = graphene.List(
        CertDataNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        cert_variety=graphene.ID(),
        is_active=graphene.Boolean()
    )

    def resolve_params_cert_data(self, info, **kwargs):
        queryset = CertData.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('cert_variety'):
            queryset = queryset.filter(cert_variety_id=kwargs['cert_variety'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('-valid_until', 'cert_variety')

    # DnVariety
    # В класс Query добавить:

    params_dn_varieties = graphene.List(
        DnVarietyNode ,
        id=graphene.ID() ,
        name=graphene.String() ,
        code=graphene.String() ,
        diameter_metric=graphene.Int() ,
        diameter_metric_min=graphene.Int() ,  # ← НОВОЕ: минимальный диаметр
        diameter_metric_max=graphene.Int() ,  # ← НОВОЕ: максимальный диаметр
        is_active=graphene.Boolean()
    )

    def resolve_params_dn_varieties(self , info , **kwargs) :
        queryset = DnVariety.objects.all()
        if kwargs.get('id') :
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name') :
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code') :
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('diameter_metric') :
            queryset = queryset.filter(diameter_metric=kwargs['diameter_metric'])
        # НОВАЯ ЛОГИКА: фильтрация по диапазону диаметров
        if kwargs.get('diameter_metric_min') :
            queryset = queryset.filter(diameter_metric__gte=kwargs['diameter_metric_min'])
        if kwargs.get('diameter_metric_max') :
            queryset = queryset.filter(diameter_metric__lte=kwargs['diameter_metric_max'])
        if kwargs.get('is_active') is not None :
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # PnVariety
    params_pn_varieties = graphene.List(
        PnVarietyNode ,
        id=graphene.ID() ,
        name=graphene.String() ,
        code=graphene.String() ,
        pressure_bar=graphene.Float() ,
        pressure_bar_min=graphene.Float() ,  # ← НОВОЕ: минимальное давление
        pressure_bar_max=graphene.Float() ,  # ← НОВОЕ: максимальное давление
        is_active=graphene.Boolean()
    )

    def resolve_params_pn_varieties(self , info , **kwargs) :
        queryset = PnVariety.objects.all()
        if kwargs.get('id') :
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name') :
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code') :
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('pressure_bar') :
            queryset = queryset.filter(pressure_bar=kwargs['pressure_bar'])
        # НОВАЯ ЛОГИКА: фильтрация по диапазону давлений
        if kwargs.get('pressure_bar_min') :
            queryset = queryset.filter(pressure_bar__gte=kwargs['pressure_bar_min'])
        if kwargs.get('pressure_bar_max') :
            queryset = queryset.filter(pressure_bar__lte=kwargs['pressure_bar_max'])
        if kwargs.get('is_active') is not None :
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # OptionVariety
    params_option_varieties = graphene.List(
        OptionVarietyNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_option_varieties(self, info, **kwargs):
        queryset = OptionVariety.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # BodyColor
    params_body_colors = graphene.List(
        BodyColorNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        ral_code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_body_colors(self, info, **kwargs):
        queryset = BodyColor.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('ral_code'):
            queryset = queryset.filter(ral_code__icontains=kwargs['ral_code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # ValveFunctionVariety
    params_valve_function_varieties = graphene.List(
        ValveFunctionVarietyNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_valve_function_varieties(self, info, **kwargs):
        queryset = ValveFunctionVariety.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # ValveActuationVariety
    params_valve_actuation_varieties = graphene.List(
        ValveActuationVarietyNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_valve_actuation_varieties(self, info, **kwargs):
        queryset = ValveActuationVariety.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # SealingClass
    params_sealing_classes = graphene.List(
        SealingClassNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        valve_function_variety=graphene.ID(),
        is_active=graphene.Boolean()
    )

    def resolve_params_sealing_classes(self, info, **kwargs):
        queryset = SealingClass.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('valve_function_variety'):
            queryset = queryset.filter(valve_function_variety_id=kwargs['valve_function_variety'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # CoatingVariety
    params_coating_varieties = graphene.List(
        CoatingVarietyNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        thickness=graphene.Int(),
        is_active=graphene.Boolean()
    )

    def resolve_params_coating_varieties(self, info, **kwargs):
        queryset = CoatingVariety.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('thickness'):
            queryset = queryset.filter(thickness=kwargs['thickness'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')

    # WarrantyTimePeriodVariety
    params_warranty_time_period_varieties = graphene.List(
        WarrantyTimePeriodVarietyNode,
        id=graphene.ID(),
        name=graphene.String(),
        code=graphene.String(),
        is_active=graphene.Boolean()
    )

    def resolve_params_warranty_time_period_varieties(self, info, **kwargs):
        queryset = WarrantyTimePeriodVariety.objects.all()
        if kwargs.get('id'):
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name'):
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('code'):
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('is_active') is not None:
            queryset = queryset.filter(is_active=kwargs['is_active'])
        return queryset.order_by('sorting_order')