# electric_actuators/types.py
import graphene
from graphene_django import DjangoObjectType
from electric_actuators.models import (
    CableGlandHolesSet, ModelLine, ModelBody, ElectricActuatorData
)

# Импортируем типы из params вместо повторного определения
from params.graphql.types import (
    IpOptionNode, BodyCoatingOptionNode, ExdOptionNode, SwitchesParametersNode,
    EnvTempParametersNode, ControlUnitInstalledOptionNode, HandWheelInstalledOptionNode,
    MechanicalIndicatorInstalledOptionNode, OperatingModeOptionNode, MountingPlateTypesNode
)


class CableGlandHolesSetNode(DjangoObjectType):
    class Meta:
        model = CableGlandHolesSet
        fields = "__all__"


class ModelLineNode(DjangoObjectType):
    class Meta:
        model = ModelLine
        fields = "__all__"

    # Используем импортированные типы из params
    allowed_ip = graphene.List(IpOptionNode)
    allowed_body_coating = graphene.List(BodyCoatingOptionNode)
    allowed_exd = graphene.List(ExdOptionNode)
    allowed_end_switches = graphene.List(SwitchesParametersNode)
    allowed_way_switches = graphene.List(SwitchesParametersNode)
    allowed_torque_switches = graphene.List(SwitchesParametersNode)
    allowed_temperature = graphene.List(EnvTempParametersNode)
    allowed_control_unit_installed = graphene.List(ControlUnitInstalledOptionNode)
    allowed_hand_wheel = graphene.List(HandWheelInstalledOptionNode)
    allowed_mechanical_indicator = graphene.List(MechanicalIndicatorInstalledOptionNode)
    allowed_operating_mode = graphene.List(OperatingModeOptionNode)

    def resolve_allowed_ip(self, info):
        return self.allowed_ip.all()

    def resolve_allowed_body_coating(self, info):
        return self.allowed_body_coating.all()

    def resolve_allowed_exd(self, info):
        return self.allowed_exd.all()

    def resolve_allowed_end_switches(self, info):
        return self.allowed_end_switches.all()

    def resolve_allowed_way_switches(self, info):
        return self.allowed_way_switches.all()

    def resolve_allowed_torque_switches(self, info):
        return self.allowed_torque_switches.all()

    def resolve_allowed_temperature(self, info):
        return self.allowed_temperature.all()

    def resolve_allowed_control_unit_installed(self, info):
        return self.allowed_control_unit_installed.all()

    def resolve_allowed_hand_wheel(self, info):
        return self.allowed_hand_wheel.all()

    def resolve_allowed_mechanical_indicator(self, info):
        return self.allowed_mechanical_indicator.all()

    def resolve_allowed_operating_mode(self, info):
        return self.allowed_operating_mode.all()


class ModelBodyNode(DjangoObjectType):
    class Meta:
        model = ModelBody
        fields = "__all__"

    allowed_cable_glands_holes = graphene.List(CableGlandHolesSetNode)
    mounting_plate = graphene.List(MountingPlateTypesNode)  # Используем импортированный тип

    def resolve_allowed_cable_glands_holes(self, info):
        return self.allowed_cable_glands_holes.all()

    def resolve_mounting_plate(self, info):
        return self.mounting_plate.all()


class ElectricActuatorDataNode(DjangoObjectType):
    class Meta:
        model = ElectricActuatorData
        fields = "__all__"