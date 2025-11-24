
import graphene
from graphene import InputObjectType
# from graphene_django import InputObjectType
from graphene_django.types import DjangoObjectType

from client_requests.graphql.types import ElectricActuatorRequirementNode
from electric_actuators.models import CableGlandHolesSet
from client_requests.models import ElectricActuatorRequirement
from params.models import (MountingPlateTypes,
    StemShapes,
    StemSize,
    SafetyPositionOption,
    MeasureUnits,
    IpOption,
    BodyCoatingOption,
    ExdOption,
    ActuatorGearboxOutputType,
    EnvTempParameters,
    MechanicalIndicatorInstalledOption,
    HandWheelInstalledOption,
    OperatingModeOption,
    BlinkerOption,
    SwitchesParameters,
    DigitalProtocolsSupportOption,
    ControlUnitTypeOption,
    ControlUnitInstalledOption,
    ControlUnitLocationOption
)



class MountingPlateInput(InputObjectType):
    id = graphene.ID(required=True)

class ElectricActuatorRequirementInput(InputObjectType):
    client_request_line_item_parent_id = graphene.ID(required=True)
    mounting_plates = graphene.List(MountingPlateInput)
    stem_shape_id = graphene.ID()
    stem_size_id = graphene.ID()
    max_stem_height = graphene.Int()
    max_stem_diameter = graphene.Int()
    safety_position_id = graphene.ID()
    time_to_open = graphene.Int()
    time_to_open_measure_unit_id = graphene.ID()
    rotations_to_open = graphene.Int()
    rotations_to_open_measure_unit_id = graphene.ID()
    rotations_angle = graphene.Int()
    ip_id = graphene.ID()
    body_coating_id = graphene.ID()
    exd_id = graphene.ID()
    output_type_id = graphene.ID()
    temperature_id = graphene.ID()
    mechanical_indicator_id = graphene.ID()
    hand_wheel_id = graphene.ID()
    operating_mode_id = graphene.ID()
    cable_glands_holes_id = graphene.ID()
    blinker_id = graphene.ID()
    end_switches_id = graphene.ID()
    way_switches_id = graphene.ID()
    torque_switches_id = graphene.ID()
    digital_protocol_support_id = graphene.ID()
    control_unit_type_id = graphene.ID()
    control_unit_installed_id = graphene.ID()
    control_unit_location_id = graphene.ID()


class CreateElectricActuatorRequirement(graphene.Mutation):
    class Arguments:
        input = ElectricActuatorRequirementInput(required=True)

    success = graphene.Boolean()
    requirement = graphene.Field(ElectricActuatorRequirementNode)
    errors = graphene.String()

    @staticmethod
    def mutate(root, info, input):
        try:
            # Создаем основной объект
            requirement = ElectricActuatorRequirement.objects.create(
                client_request_line_item_parent_id=input.client_request_line_item_parent_id,
                stem_shape_id=input.stem_shape_id,
                stem_size_id=input.stem_size_id,
                max_stem_height=input.max_stem_height,
                max_stem_diameter=input.max_stem_diameter,
                safety_position_id=input.safety_position_id,
                time_to_open=input.time_to_open,
                time_to_open_measure_unit_id=input.time_to_open_measure_unit_id,
                rotations_to_open=input.rotations_to_open,
                rotations_to_open_measure_unit_id=input.rotations_to_open_measure_unit_id,
                rotations_angle=input.rotations_angle,
                ip_id=input.ip_id,
                body_coating_id=input.body_coating_id,
                exd_id=input.exd_id,
                output_type_id=input.output_type_id,
                temperature_id=input.temperature_id,
                mechanical_indicator_id=input.mechanical_indicator_id,
                hand_wheel_id=input.hand_wheel_id,
                operating_mode_id=input.operating_mode_id,
                cable_glands_holes_id=input.cable_glands_holes_id,
                blinker_id=input.blinker_id,
                end_switches_id=input.end_switches_id,
                way_switches_id=input.way_switches_id,
                torque_switches_id=input.torque_switches_id,
                digital_protocol_support_id=input.digital_protocol_support_id,
                control_unit_type_id=input.control_unit_type_id,
                control_unit_installed_id=input.control_unit_installed_id,
                control_unit_location_id=input.control_unit_location_id
            )

            # Обрабатываем ManyToMany поля
            if input.mounting_plates:
                plate_ids = [mp.id for mp in input.mounting_plates]
                requirement.mounting_plate.set(plate_ids)

            return CreateElectricActuatorRequirement(
                success=True,
                requirement=requirement,
                errors=None
            )
        except Exception as e:
            return CreateElectricActuatorRequirement(
                success=False,
                requirement=None,
                errors=str(e)
            )


class UpdateElectricActuatorRequirement(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = ElectricActuatorRequirementInput(required=True)

    success = graphene.Boolean()
    requirement = graphene.Field(ElectricActuatorRequirementNode)
    errors = graphene.String()

    @staticmethod
    def mutate(root, info, id, input):
        try:
            requirement = ElectricActuatorRequirement.objects.get(pk=id)

            # Обновляем поля
            if input.stem_shape_id is not None:
                requirement.stem_shape_id = input.stem_shape_id
            if input.stem_size_id is not None:
                requirement.stem_size_id = input.stem_size_id
            if input.max_stem_height is not None:
                requirement.max_stem_height = input.max_stem_height
            # ... аналогично для всех остальных полей

            # Обновляем ManyToMany
            if input.mounting_plates is not None:
                plate_ids = [mp.id for mp in input.mounting_plates]
                requirement.mounting_plate.set(plate_ids)

            requirement.save()
            return UpdateElectricActuatorRequirement(
                success=True,
                requirement=requirement,
                errors=None
            )
        except ElectricActuatorRequirement.DoesNotExist:
            return UpdateElectricActuatorRequirement(
                success=False,
                requirement=None,
                errors="Requirement not found"
            )
        except Exception as e:
            return UpdateElectricActuatorRequirement(
                success=False,
                requirement=None,
                errors=str(e)
            )


class DeleteElectricActuatorRequirement(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.String()

    @staticmethod
    def mutate(root, info, id):
        try:
            requirement = ElectricActuatorRequirement.objects.get(pk=id)
            requirement.delete()
            return DeleteElectricActuatorRequirement(
                success=True,
                errors=None
            )
        except ElectricActuatorRequirement.DoesNotExist:
            return DeleteElectricActuatorRequirement(
                success=False,
                errors="Requirement not found"
            )
        except Exception as e:
            return DeleteElectricActuatorRequirement(
                success=False,
                errors=str(e)
            )