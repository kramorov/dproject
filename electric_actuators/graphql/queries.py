# electric_actuators/query.py
import graphene

from electric_actuators.graphql.types import (
    CableGlandHolesSetNode, ModelLineNode, ModelBodyNode, ElectricActuatorDataNode
)
from electric_actuators.models import (
    CableGlandHolesSet, ModelLine, ModelBody, ElectricActuatorData
)

from params.graphql.types import (
    ThreadSizeNode, IpOptionNode, BodyCoatingOptionNode, ExdOptionNode, BlinkerOptionNode,
    SwitchesParametersNode, EnvTempParametersNode, ControlUnitInstalledOptionNode,
    HandWheelInstalledOptionNode, MechanicalIndicatorInstalledOptionNode,
    OperatingModeOptionNode, PowerSuppliesNode, MeasureUnitsNode,
    ActuatorGearboxOutputTypeNode, MountingPlateTypesNode, StemShapesNode, StemSizeNode, MountingPlateTypesNode,
    ActuatorGearboxOutputTypeNode
)

from params.models import (
    ThreadSize, IpOption, BodyCoatingOption, ExdOption, BlinkerOption,
    SwitchesParameters, EnvTempParameters, ControlUnitInstalledOption,
    HandWheelInstalledOption, MechanicalIndicatorInstalledOption,
    OperatingModeOption, PowerSupplies, MeasureUnits,
    ActuatorGearboxOutputType, MountingPlateTypes, StemShapes, StemSize
)

from producers.graphql.types import (BrandsNode)
from producers.models import (Brands)


class Query(graphene.ObjectType):
    # CableGlandHolesSet queries
    ea_cable_gland_holes_set = graphene.Field(CableGlandHolesSetNode, id=graphene.Int())

    def resolve_ea_cable_gland_holes_set(self, info, id=None):
        if id:
            return CableGlandHolesSet.objects.get(id=id)
        return None

    all_cable_gland_holes_sets = graphene.List(CableGlandHolesSetNode)

    def resolve_ea_all_cable_gland_holes_sets(self, info):
        return CableGlandHolesSet.objects.all()

    # ModelLine queries
    ea_model_line = graphene.Field(ModelLineNode, id=graphene.Int())

    def resolve_ea_model_line(self, info, id=None):
        if id:
            return ModelLine.objects.get(id=id)
        return None

    ea_all_model_lines = graphene.List(ModelLineNode)

    def resolve_ea_all_model_lines(self, info):
        return ModelLine.objects.all()

    # ModelBody queries
    ea_model_body = graphene.Field(ModelBodyNode, id=graphene.Int())

    def resolve_ea_model_body(self, info, id=None):
        if id:
            return ModelBody.objects.get(id=id)
        return None

    ea_all_model_bodies = graphene.List(ModelBodyNode)

    def resolve_ea_all_model_bodies(self, info):
        return ModelBody.objects.all()

    # ElectricActuatorData queries
    ea_electric_actuator_data = graphene.Field(ElectricActuatorDataNode, id=graphene.Int())

    def resolve_ea_electric_actuator_data(self, info, id=None):
        if id:
            return ElectricActuatorData.objects.get(id=id)
        return None

    ea_all_electric_actuator_data = graphene.List(ElectricActuatorDataNode)

    def resolve_ea_all_electric_actuator_data(self, info):
        return ElectricActuatorData.objects.all()

    # Новый query для фильтрации по model_line.id
    ea_models_by_model_line = graphene.List(
        ElectricActuatorDataNode,
        model_line_id=graphene.Int(required=True),
        description="Получить ElectricActuatorData по ID модели линии"
    )

    def resolve_ea_models_by_model_line(self, info, model_line_id):
        return ElectricActuatorData.objects.filter(model_line_id=model_line_id)
