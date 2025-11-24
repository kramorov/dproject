import graphene
from graphene_django import DjangoObjectType


from djangoProject1.common_models.graphql_utils import generate_model_types
from ..models import ClientRequestsType, ClientRequestsStatus, ClientRequestItem, ElectricActuatorRequirement, \
   ClientRequests


# Типы объектов
class ClientRequestsTypeNode(DjangoObjectType):
    class Meta:
        model = ClientRequestsType
        fields = '__all__'  # Или явно перечислите нужные пол

class ClientRequestsStatusNode(DjangoObjectType):
    class Meta:
        model = ClientRequestsStatus
        fields = '__all__'  # Или явно перечислите нужные пол

class ClientRequestItemNode(DjangoObjectType):
    class Meta:
        model = ClientRequestItem
        # interfaces = (graphene.relay.Node,)
        fields = '__all__'  # Или явно перечислите нужные пол

class ElectricActuatorRequirementNode(DjangoObjectType):
    class Meta:
        model = ElectricActuatorRequirement
        # interfaces = (graphene.relay.Node,)
        fields = '__all__'  # Или явно перечислите нужные пол

# class ValveRequirementNode(DjangoObjectType):
#     class Meta:
#         model = ValveRequirement
#         # interfaces = (graphene.relay.Node,)
#         fields = '__all__'  # Или явно перечислите нужные пол

# class ValveSelectionNode(DjangoObjectType):
#     class Meta:
#         model = ValveSelection
#         # interfaces = (graphene.relay.Node,)
#         fields = '__all__'  # Или явно перечислите нужные пол


class ClientRequestsNode(DjangoObjectType):
    request_lines = graphene.List(ClientRequestItemNode)

    class Meta:
        model = ClientRequests
        # interfaces = (graphene.relay.Node,)
        fields = '__all__'  # Или явно перечислите нужные пол

    def resolve_request_lines(self, info):
        return self.request_lines.all()










