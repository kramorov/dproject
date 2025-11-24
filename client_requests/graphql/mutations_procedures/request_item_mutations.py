import graphene
from graphene import relay
from graphql import GraphQLError
from client_requests.models import ClientRequests, ClientRequestItem
from client_requests.graphql.types import ClientRequestsNode


class ClientRequestsItemInput(graphene.InputObjectType) :
    request_parent = graphene.ID(description="ID Запрос клиента")
    request_line_number = graphene.String(description="Номер строки в запросе клиента")
    request_line_ol = graphene.String(description="Идентификатор (номер) ОЛ для этой строки в запросе клиента")
    source_request_line_number = graphene.String(description="Номер строки в запросе клиента")
    request_line_text = graphene.String(description="Текстовое описание строки запроса. Сюда можно скопировать текст, чтобы потом перенести в поля требований")

class CreateClientRequestItem(graphene.Mutation) :
    class Arguments :
        input = ClientRequestsItemInput(required=True)

    client_request = graphene.Field(ClientRequestsNode)

    @classmethod
    def mutate(cls , root , info , input) :
        try :
            client_request_item = ClientRequestItem(
                request_parent=input.get('request_parent') ,
                request_line_number=input.get('request_line_number') ,
                request_line_ol=input.get('request_line_ol') ,
                source_request_line_number=input.get('source_request_line_number') ,
                request_line_text=input.get('request_line_text') ,

            )
            client_request_item.full_clean()
            client_request_item.save()
            return cls(client_request_item=client_request_item)
        except Exception as e :
            raise GraphQLError(f"Ошибка создания строки запроса: {str(e)}")


class UpdateClientRequestItem(graphene.Mutation) :
    class Arguments :
        id = graphene.ID(required=True , description="ID обновляемой строки запроса")
        input = ClientRequestsItemInput(required=True)

    client_request_item = graphene.Field(ClientRequestsNode)

    @classmethod
    def mutate(cls , root , info , id , input) :
        try :
            client_request_item = ClientRequestItem.objects.get(pk=id)

            # Обновляем простые поля
            fields = ['request_line_number' , 'request_line_number' , 'request_line_ol' , 'source_request_line_number', 'request_line_text']
            for field in fields :
                if field in input :
                    setattr(client_request_item , field , input[field])

            # Обновляем связи
            relation_fields = {
                'request_parent_id' : 'request_parent'
            }

            for input_field , model_field in relation_fields.items() :
                if input_field in input :
                    setattr(client_request_item , model_field + '_id' , input[input_field])

            client_request_item.full_clean()
            client_request_item.save()
            return cls(client_request=client_request_item)

        except ClientRequestItem.DoesNotExist :
            raise GraphQLError(f"Ошибка обновления строки запроса. Строка запроса с ID {id} не найдена")
        except Exception as e :
            raise GraphQLError(f"Ошибка обновления строки запроса: {str(e)}")


class DeleteClientRequestItem(graphene.Mutation) :
    class Arguments :
        id = graphene.ID(required=True , description="ID удаляемой строки запроса")

    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    def mutate(cls , root , info , id) :
        try :
            client_request_item = ClientRequestItem.objects.get(pk=id)
            client_request_item.delete()
            return cls(success=True , message="Строка запроса успешно удалена")
        except ClientRequestItem.DoesNotExist :
            return cls(success=False , message=f"Ошибка удаления. Строка запроса с ID {id} не найдена")
        except Exception as e :
            raise GraphQLError(f"Ошибка удаления строки запроса: {str(e)}")


class CopyClientRequestItem(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID строки запроса для копирования")

    client_request_item = graphene.Field(ClientRequestsNode)  # Используем ваш существующий тип Node

    @classmethod
    def mutate(cls, root, info, id):
        try:
            # 1. Получаем исходный объект
            original_item = ClientRequestItem.objects.get(pk=id)

            # 2. Создаем копию, исключая id (он создастся автоматически)
            new_item = ClientRequestItem(
                request_parent=original_item.request_parent,
                request_line_number=original_item.request_line_number,
                request_line_ol=original_item.request_line_ol,
                source_request_line_number=original_item.source_request_line_number,
                request_line_text=original_item.request_line_text,
                # Копируем все остальные поля...
            )

            # 3. Сохраняем новый объект
            new_item.full_clean()
            new_item.save()

            return cls(client_request_item=new_item)

        except ClientRequestItem.DoesNotExist:
            raise GraphQLError(f"Строка запроса с ID {id} не найдена")
        except Exception as e:
            raise GraphQLError(f"Ошибка копирования строки запроса: {str(e)}")