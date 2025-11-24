# Входные типы для мутаций
import graphene

from client_requests.graphql.types import ClientRequests_Type
from client_requests.models import ClientRequests

class ClientRequestsInput(graphene.InputObjectType):
    symbolic_code = graphene.String()
    end_customer = graphene.String()
    request_status_id = graphene.ID()
    request_type_id = graphene.ID()
    request_text = graphene.String()
    request_from_client_company_id = graphene.ID()
    request_responsible_person_id = graphene.ID()
    request_date = graphene.Date(required=True)


class ClientRequestItemInput(graphene.InputObjectType):
    request_parent_id = graphene.ID(required=True)
    request_line_number = graphene.Int()
    request_line_ol = graphene.String()
    source_request_line_number = graphene.Int()
    request_line_text = graphene.String()


class ValveRequirementInput(graphene.InputObjectType):
    client_request_line_item_parent_id = graphene.ID(required=True)
    valve_model_model_line_id = graphene.ID()
    valve_model_model_line_str = graphene.String()
    # Добавьте остальные поля из AbstractValveModel
    request_parent = graphene.ID(required=True)
    client_request_line_parent = graphene.ID(required=True)


# Мутации
class CreateClientRequest(graphene.Mutation):
    class Arguments:
        input = ClientRequestsInput(required=True)

    client_request = graphene.Field(ClientRequests_Type)

    @staticmethod
    def mutate(root, info, input):
        try:
            # Преобразование ID в объекты
            request_status = None
            if input.get('request_status_id'):
                request_status = graphene.Node.get_node_from_global_id(info, input.request_status_id)

            request_type = None
            if input.get('request_type_id'):
                request_type = graphene.Node.get_node_from_global_id(info, input.request_type_id)

            request_from_client_company = None
            if input.get('request_from_client_company_id'):
                request_from_client_company = graphene.Node.get_node_from_global_id(info,
                                                                                    input.request_from_client_company_id)

            request_responsible_person = None
            if input.get('request_responsible_person_id'):
                request_responsible_person = graphene.Node.get_node_from_global_id(info,
                                                                                   input.request_responsible_person_id)

            # Создание объекта

            client_request = ClientRequests( # Это модель из DRF
                symbolic_code=input.get('symbolic_code'),
                end_customer=input.get('end_customer'),
                request_status=request_status,
                request_type=request_type,
                request_text=input.get('request_text'),
                request_from_client_company=request_from_client_company,
                request_responsible_person=request_responsible_person,
                request_date=input.request_date
            )
            client_request.save()

            return CreateClientRequest(client_request=client_request)
        except Exception as e:
            raise Exception(f"Error creating client request: {str(e)}")


class UpdateClientRequest(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = ClientRequestsInput(required=True)

    client_request = graphene.Field(ClientRequests_Type)
	
    @staticmethod
    def mutate(root, info, id, input):
        print(f"Received ID: {id}, type: {type(id)}")  # Перед обработкой
        try:
            # Позволяем принимать как Global ID, так и обычные ID
            try:
                # Пробуем декодировать как Global ID
                client_request = graphene.Node.get_node_from_global_id(info, id)
            except:
                # Если не получилось, пробуем как обычный ID
                client_request = ClientRequests.objects.get(pk=id)
            
            if not client_request:
                raise Exception("Client request not found")

            # Обновление полей
            if 'symbolic_code' in input:
                client_request.symbolic_code = input.symbolic_code
            if 'end_customer' in input:
                client_request.end_customer = input.end_customer
            if 'request_text' in input:
                client_request.request_text = input.request_text
            if 'request_date' in input:
                client_request.request_date = input.request_date

            # Обновление связей
            if 'request_status_id' in input:
                client_request.request_status = graphene.Node.get_node_from_global_id(info,
                                                                                      input.request_status_id) if input.request_status_id else None

            if 'request_type_id' in input:
                client_request.request_type = graphene.Node.get_node_from_global_id(info,
                                                                                    input.request_type_id) if input.request_type_id else None

            if 'request_from_client_company_id' in input:
                client_request.request_from_client_company = graphene.Node.get_node_from_global_id(info,
                                                                                                   input.request_from_client_company_id) if input.request_from_client_company_id else None

            if 'request_responsible_person_id' in input:
                client_request.request_responsible_person = graphene.Node.get_node_from_global_id(info,
                                                                                                  input.request_responsible_person_id) if input.request_responsible_person_id else None

            client_request.save()
            return UpdateClientRequest(client_request=client_request)
        except Exception as e:
            raise Exception(f"Error updating client request: {str(e)}")


class DeleteClientRequest(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, info, id):
        try:
            client_request = graphene.Node.get_node_from_global_id(info, id)
            if not client_request:
                raise Exception("Client request not found")

            client_request.delete()
            return DeleteClientRequest(success=True)
        except Exception as e:
            raise Exception(f"Error deleting client request: {str(e)}")


class Mutation(graphene.ObjectType):
    create_client_request = CreateClientRequest.Field()
    update_client_request = UpdateClientRequest.Field()
    delete_client_request = DeleteClientRequest.Field()




