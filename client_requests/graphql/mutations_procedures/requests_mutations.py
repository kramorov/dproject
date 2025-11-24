import graphene
from graphene import relay
from graphql import GraphQLError
from client_requests.models import ClientRequests, ClientRequestItem, ClientRequestsStatus
from client_requests.graphql.types import ClientRequestsNode
from django.db import transaction

class ClientRequestsInput(graphene.InputObjectType) :
    symbolic_code = graphene.String(description="Символьный код заявки")
    end_customer = graphene.String(description="Конечный заказчик")
    request_status_id = graphene.ID(description="ID статуса заявки")
    request_type_id = graphene.ID(description="ID типа заявки")
    request_text = graphene.String(description="Текст заявки")
    request_from_client_company_id = graphene.ID(description="ID компании-клиента")
    request_responsible_person_id = graphene.ID(description="ID ответственного лица")
    request_date = graphene.Date(required=True , description="Дата заявки")

class ClientRequestQueryPayload(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    new_id = graphene.ID()

class CreateClientRequestNewPayload(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    new_id = graphene.ID()
    client_request = graphene.Field(ClientRequestsNode)

class CreateClientRequest(graphene.Mutation) :
    class Arguments :
        input = ClientRequestsInput(required=True)

    # client_request = graphene.Field(ClientRequestsNode)
    # class Output:
    #     success = graphene.Boolean()
    #     message = graphene.String()
    #     new_id = graphene.ID()
    #     client_request = graphene.Field(ClientRequestsNode)


    Output = CreateClientRequestNewPayload  # Или другой подходящий тип
    @classmethod
    def mutate(cls , root , info , input) :
        try :
            client_request = ClientRequests(
                symbolic_code=input.get('symbolic_code') ,
                end_customer=input.get('end_customer') ,
                request_text=input.get('request_text') ,
                request_date=input.get('request_date') ,
                request_status_id=input.get('request_status_id') ,
                request_type_id=input.get('request_type_id') ,
                request_from_client_company_id=input.get('request_from_client_company_id') ,
                request_responsible_person_id=input.get('request_responsible_person_id')
            )
            client_request.full_clean()
            client_request.save()
            # print('Create request id=',client_request.id)
            # res = ClientRequestQueryPayload(
            #     client_request=client_request,
            #     success=True,
            #     message="Запрос успешно создан.",
            #     new_id=client_request.id)
            return CreateClientRequestNewPayload(
                success=True,
                message="Запрос успешно создан",
                new_id=client_request.id,
                client_request=client_request
            )
            # return CreateClientRequest(
            #     client_request=client_request,
            #     success=True,
            #     message="Запрос успешно создан.",
            #     new_id=client_request.id
            # )
        except ValidationError as e:
            # Обработка ошибок валидации
            return CreateClientRequestNewPayload(
                success=False,
                message=f"Ошибка валидации: {str(e)}",
                new_id=None,
                client_request=None
            )
        except Exception as e :
            # Обработка других ошибок
            return CreateClientRequestNewPayload(
                success=False,
                message=f"Ошибка при создании запроса: {str(e)}",
                new_id=None,
                client_request=None
            )


class UpdateClientRequest(graphene.Mutation) :
    class Arguments :
        id = graphene.ID(required=True , description="ID обновляемой заявки")
        input = ClientRequestsInput(required=True)

    client_request = graphene.Field(ClientRequestsNode)

    @classmethod
    def mutate(cls , root , info , id , input) :
        try :
            client_request = ClientRequests.objects.get(pk=id)

            # Обновляем простые поля
            fields = ['symbolic_code' , 'end_customer' , 'request_text' , 'request_date']
            for field in fields :
                if field in input :
                    setattr(client_request , field , input[field])

            # Обновляем связи
            relation_fields = {
                'request_status_id' : 'request_status' ,
                'request_type_id' : 'request_type' ,
                'request_from_client_company_id' : 'request_from_client_company' ,
                'request_responsible_person_id' : 'request_responsible_person'
            }

            for input_field , model_field in relation_fields.items() :
                if input_field in input :
                    setattr(client_request , model_field + '_id' , input[input_field])

            client_request.full_clean()
            client_request.save()
            return cls(client_request=client_request)

        except ClientRequests.DoesNotExist :
            raise GraphQLError("Заявка не найдена")
        except Exception as e :
            raise GraphQLError(f"Ошибка обновления заявки: {str(e)}")


class DeleteClientRequest(graphene.Mutation) :
    class Arguments :
        id = graphene.ID(required=True , description="ID удаляемой заявки")

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    def mutate(cls , root , info , id) :
        try :
            client_request = ClientRequests.objects.get(pk=id)
            client_request.delete()
            return cls(success=True , message="Заявка успешно удалена")
        except ClientRequests.DoesNotExist :
            return cls(success=False , message="Заявка не найдена")
        except Exception as e :
            raise GraphQLError(f"Ошибка удаления заявки: {str(e)}")



class CopyClientRequest(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID запроса для копирования")
        new_status = graphene.String(required=False, description="Новый статус для копии (по умолчанию 'New')")

    client_request = graphene.Field(ClientRequestsNode)
    Output = ClientRequestQueryPayload  # Указываем тип возвращаемых данных

    @classmethod
    def mutate(cls, root, info, id, new_status='New'):
        try:
            with (transaction.atomic()):  # Чтобы обеспечить целостность данных
                # 1. Получаем исходный запрос
                original_request = ClientRequests.objects.get(pk=id)

                # 2. Создаем копию основного объекта
                new_request = ClientRequests(
                    symbolic_code=f"Копия {original_request.symbolic_code}" if original_request.symbolic_code else None,
                    end_customer=original_request.end_customer,
                    request_type=original_request.request_type,
                    request_text=original_request.request_text,
                    request_from_client_company=original_request.request_from_client_company,
                    request_responsible_person=original_request.request_responsible_person,
                    request_date=original_request.request_date,
                    request_status_id=ClientRequestsStatus.objects.get(symbolic_code=new_status).id
                )
                new_request.full_clean()
                new_request.save()

                # 3. Копируем все связанные строки запроса (ClientRequestItem)
                for item in original_request.request_lines.all():
                    ClientRequestItem.objects.create(
                        request_parent=new_request,
                        item_no=item.item_no,
                        request_line_number=item.request_line_number,
                        request_line_ol=item.request_line_ol,
                        source_request_line_number=item.source_request_line_number,
                        request_line_text=item.request_line_text
                    )

                return ClientRequestQueryPayload(
                    success=True,
                    message="Запрос успешно скопирован",
                    new_id=new_request.id  #cls(client_request=new_request)
                )



        except ClientRequests.DoesNotExist:
            # raise GraphQLError(f"Запрос с ID {id} не найден")
            return ClientRequestQueryPayload(
                success=False,
                message=f"Запрос с ID {id} не найден",
                new_id=None)
        except ClientRequestsStatus.DoesNotExist:
            # raise GraphQLError(f"Статус {new_status} не найден")
            return ClientRequestQueryPayload(
                success=False,
                message=f"Статус {new_status} не найден",
                new_id=None)
        except Exception as e:
            # raise GraphQLError(f"Ошибка копирования запроса: {str(e)}")
            return ClientRequestQueryPayload(
                success=False,
                message=f"Ошибка копирования запроса: {str(e)}",
                new_id=None)
