import graphene

from client_requests.graphql.types import ClientRequestsTypeNode, ClientRequestsStatusNode, ClientRequestsNode, \
    ClientRequestItemNode, ElectricActuatorRequirementNode
from client_requests.models import ClientRequestsType, ClientRequestsStatus, ClientRequests, ClientRequestItem, \
    ElectricActuatorRequirement

class Query(graphene.ObjectType):
    # Одиночные объекты
    req_client_requests_type = graphene.Field(
        ClientRequestsTypeNode,
        id=graphene.ID(required=True),
        description="Получение типа заявки по ID"
    )
    req_client_requests_status = graphene.Field(
        ClientRequestsStatusNode,
        id=graphene.ID(required=True),
        description="Получение статуса заявки по ID"
    )
    req_client_request = graphene.Field(
        ClientRequestsNode,
        id=graphene.ID(required=True),
        description="Получение заявки клиента по ID"
    )
    req_client_request_item = graphene.Field(
        ClientRequestItemNode,
        id=graphene.ID(required=True),
        description="Получение пункта заявки по ID"
    )
    # req_valve_requirement = graphene.Field(
    #     ValveRequirementNode,
    #     id=graphene.ID(required=True),
    #     description="Получение требований к клапану по ID"
    # )
    req_electric_actuator_requirement = graphene.Field(
        ElectricActuatorRequirementNode,
        id=graphene.ID(required=True),
        description="Получение одной записи требований к электроприводу по ее ID"
    )
    req_all_electric_actuator_requirements = graphene.List(
        ElectricActuatorRequirementNode,
        description="Получение всех записей требований к электроприводам"
    )
    req_all_electric_actuator_requirements_by_parent = graphene.List(
        ElectricActuatorRequirementNode,
        parent_id=graphene.ID(required=True),
        description="Получение всех записей требований к электроприводам требований по ID родительского элемента"
    )

    # Списки объектов
    req_all_client_requests_types = graphene.List(
        ClientRequestsTypeNode,
        description="Получение всех типов заявок"
    )
    req_all_client_requests_statuses = graphene.List(
        ClientRequestsStatusNode,
        description="Получение всех статусов заявок"
    )
    req_all_client_requests = graphene.List(
        ClientRequestsNode,
        description="Получение всех заявок клиентов"
    )
    req_all_client_request_items = graphene.List(
        ClientRequestItemNode,
        description="Получение всех пунктов заявок"
    )
    # req_all_valve_requirements = graphene.List(
    #     ValveRequirementNode,
    #     description="Получение всех требований к клапанам"
    # )
    # req_all_electric_actuator_requirements = graphene.List(
    #     ElectricActuatorRequirementNode,
    #     description="Получение всех требований к электроприводам"
    # )

    # Резольверы для одиночных объектов
    def resolve_req_client_requests_type(self, info, id):
        try:
            return ClientRequestsType.objects.get(pk=id)
        except ClientRequestsType.DoesNotExist:
            return None

    def resolve_req_client_requests_status(self, info, id):
        try:
            return ClientRequestsStatus.objects.get(pk=id)
        except ClientRequestsStatus.DoesNotExist:
            return None

    def resolve_req_client_request(self, info, id):
        try:
            return ClientRequests.objects.get(pk=id)
        except ClientRequests.DoesNotExist:
            return None

    def resolve_req_client_request_item(self, info, id):
        try:
            return ClientRequestItem.objects.get(pk=id)
        except ClientRequestItem.DoesNotExist:
            return None

    def resolve_req_valve_requirement(self, info, id):
        try:
            return ValveRequirement.objects.get(pk=id)
        except ValveRequirement.DoesNotExist:
            return None

    def resolve_req_electric_actuator_requirement(self, info, id):
        try:
            return ElectricActuatorRequirement.objects.get(pk=id)
        except ElectricActuatorRequirement.DoesNotExist:
            return None

    # Резольверы для списков
    def resolve_req_all_client_requests_types(self, info):
        return ClientRequestsType.objects.all()

    def resolve_req_all_client_requests_statuses(self, info):
        return ClientRequestsStatus.objects.all()

    def resolve_req_all_client_requests(self, info):
        return ClientRequests.objects.all()

    def resolve_req_all_client_request_items(self, info):
        return ClientRequestItem.objects.all()

    # def resolve_req_all_valve_requirements(self, info):
    #     return ValveRequirement.objects.all()

    def resolve_req_all_electric_actuator_requirements(self, info):
        return ElectricActuatorRequirement.objects.all()

    def resolve_electric_actuator_requirement(self, info, id):
        try:
            return ElectricActuatorRequirement.objects.get(pk=id)
        except ElectricActuatorRequirement.DoesNotExist:
            return None
        except Exception as e:
            raise Exception(f"Ошибка при получении требования: {str(e)}")

    def resolve_all_electric_actuator_requirements(self, info):
        try:
            return ElectricActuatorRequirement.objects.all()
        except Exception as e:
            raise Exception(f"Ошибка при получении списка требований: {str(e)}")

    def resolve_req_all_electric_actuator_requirements_by_parent(self, info, parent_id):
        return ElectricActuatorRequirement.objects.filter(
            client_request_line_item_parent_id=parent_id
        )