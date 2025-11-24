import graphene
from graphene import relay
from graphql import GraphQLError

from client_requests.graphql.mutations_procedures.ea_requirement_mutations import DeleteElectricActuatorRequirement, \
    UpdateElectricActuatorRequirement, CreateElectricActuatorRequirement
from client_requests.graphql.mutations_procedures.request_item_mutations import CreateClientRequestItem, \
    UpdateClientRequestItem, DeleteClientRequestItem, CopyClientRequestItem
from client_requests.graphql.mutations_procedures.requests_mutations import CreateClientRequest, UpdateClientRequest, \
    DeleteClientRequest, CopyClientRequest
from client_requests.models import ClientRequests
from client_requests.graphql.types import ClientRequestsNode


class Mutation(graphene.ObjectType) :
    req_create_client_request = CreateClientRequest.Field(
        description="Создание нового запроса клиента"
    )
    req_update_client_request = UpdateClientRequest.Field(
        description="Обновление существующего запроса клиента"
    )
    req_delete_client_request = DeleteClientRequest.Field(
        description="Удаление запроса клиента"
    )
    req_copy_client_request = CopyClientRequest.Field(
        description="Копирование запроса клиента"
    )

    req_create_client_request_item = CreateClientRequestItem.Field(
        description="Создание новой строки запроса клиента"
    )
    req_update_client_request_item = UpdateClientRequestItem.Field(
        description="Обновление существующей строки запроса клиента"
    )
    req_delete_client_request_item = DeleteClientRequestItem.Field(
        description="Удаление строки запроса клиента"
    )

    req_copy_client_request_item = CopyClientRequestItem.Field(
        description="Копирование строки запроса клиента"
    )
    req_create_electric_actuator_requirement = CreateElectricActuatorRequirement.Field(
        description="Создание требований к электроприводу для строки запроса клиента"
    )
    req_update_electric_actuator_requirement = UpdateElectricActuatorRequirement.Field(
        description="Обновление требований к электроприводу для строки запроса клиента"
    )
    req_delete_electric_actuator_requirement = DeleteElectricActuatorRequirement.Field(
        description="Удаление требований к электроприводу для строки запроса клиента"
    )