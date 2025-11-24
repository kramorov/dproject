from rest_framework import serializers, status, viewsets
from rest_framework.generics import ListCreateAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework.pagination import PageNumberPagination
from .serializers import ClientRequestTypeSerializer, ClientRequestsSerializer, \
    ClientRequestItemSerializer, ElectricActuatorRequirementSerializer,  \
    ClientRequestListSerializer, ClientRequestItemListSerializer, ClientRequestItemSerializer_Short, \
    ClientRequestStatusSerializer, ClientRequestSaveSerializer

from .models import ClientRequestsType, ClientRequests, ClientRequestItem, ElectricActuatorRequirement, \
    ClientRequestsStatus


class ClientRequestsStatusList(ListAPIView):
    queryset = ClientRequestsStatus.objects.all()
    serializer_class = ClientRequestStatusSerializer

class ClientRequestEditAdd(viewsets.ModelViewSet):
    queryset = ClientRequests.objects.all()
    serializer_class = ClientRequestsSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClientRequestTypeAPIView(APIView):

    def get(self, request, pk):
        try:
            item = ClientRequestsType.objects.get(pk=pk)
            serializer = ClientRequestTypeSerializer(item)
            return Response(serializer.data)
        except ClientRequestsType.DoesNotExist:
            return Response(status=404)

    def put(self, request, pk):
        try:
            item = ClientRequestsType.objects.get(pk=pk)
        except ClientRequestsType.DoesNotExist:
            return Response(status=404)
        serializer = ClientRequestTypeSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        try:
            item = ClientRequestsType.objects.get(pk=pk)
        except ClientRequestsType.DoesNotExist:
            return Response(status=404)
        item.delete()
        return Response(status=204)


class ClientRequestTypeAPIListView(APIView):

    def get(self, request):
        items = ClientRequestsType.objects.order_by('pk')
        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(items, request)
        serializer = ClientRequestTypeSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = ClientRequestTypeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class ClientRequestAPIView(APIView):

    def get(self, request, pk=None, format=None):
        # Получение структуры (если pk=None)
        if pk is None:
            return self._get_structure_response()

        # Получение конкретного объекта
        try:
            item = ClientRequests.objects.get(pk=pk)
            serializer = ClientRequestsSerializer(item)
            return Response({
                'data': serializer.data,
                'structure': self._get_structure()  # Добавляем структуру
            })
        except ClientRequests.DoesNotExist:
            return Response(status=404)

    def _get_structure(self):
        """Вспомогательный метод для получения структуры"""
        return ClientRequestsSerializer.get_structure()

    def _get_structure_response(self):
        """Отдельный ответ только для структуры"""
        return Response({
            'structure': self._get_structure(),
            # 'defaults': ClientRequestsSerializer.get_default_values()
        })
    def put(self, request, pk):
        try:
            item = ClientRequests.objects.get(pk=pk)
        except ClientRequests.DoesNotExist:
            return Response(status=404)
        serializer = ClientRequestsSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        try:
            item = ClientRequests.objects.get(pk=pk)
        except ClientRequests.DoesNotExist:
            return Response(status=404)
        item.delete()
        return Response(status=204)


class ClientRequestsAPIListView(APIView):

    def get(self, request):
        items = ClientRequests.objects.order_by('pk')
        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(items, request)
        serializer = ClientRequestListSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = ClientRequestSaveSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def patch(self, request, pk):
        try:
            instance = ClientRequests.objects.get(pk=pk)
        except ClientRequests.DoesNotExist:
            return Response(
                {'error': 'Запрос с указанным ID не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверяем, есть ли данные для обновления
        if not request.data:
            return Response(
                {'error': 'Не предоставлены данные для обновления'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ClientRequestSaveSerializer(
            instance,
            data=request.data,
            partial=True  # Важно для PATCH-запросов
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ClientRequestLinesOnly_List(ListCreateAPIView):
    serializer_class = ClientRequestItemSerializer_Short

    def get_queryset(self):
        queryset = ClientRequestItem.objects.all()
        parent_id = self.request.query_params.get('parent_id')
        if parent_id:
            queryset = queryset.filter(request_parent_id=parent_id)
        return queryset

class ClientRequestItemAPIView(APIView):

    def get(self, request):


        try:
            request_type = request.query_params.get('by_id')
            request_id = request.query_params.get('request_id')
            item = ClientRequestItem.objects.get(pk=request_id)
            serializer = ClientRequestItemSerializer(item)
            return Response(serializer.data)
        except ClientRequestItem.DoesNotExist:
            return Response(status=404)

    def put(self, request, pk):
        try:
            item = ClientRequestItem.objects.get(pk=pk)
        except ClientRequestItem.DoesNotExist:
            return Response(status=404)
        serializer = ClientRequestItemSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        try:
            item = ClientRequestItem.objects.get(pk=pk)
        except ClientRequestItem.DoesNotExist:
            return Response(status=404)
        item.delete()
        return Response(status=204)


class ClientRequestItemListView(APIView):
    def get(self, request, *args, **kwargs):
        serializer = ClientRequestItemListSerializer(data=request.query_params)
        print(request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class ClientRequestItemAPIListView(APIView):

    def get(self, request):
        items = ClientRequestItem.objects.order_by('pk')
        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(items, request)
        serializer = ClientRequestItemSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = ClientRequestItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class ElectricActuatorRequirementAPIView(APIView):

    def get(self, request, pk):
        try:
            item = ElectricActuatorRequirement.objects.get(pk=id)
            serializer = ElectricActuatorRequirementSerializer(item)
            return Response(serializer.data)
        except ElectricActuatorRequirement.DoesNotExist:
            return Response(status=404)

    def put(self, request, pk):
        try:
            item = ElectricActuatorRequirement.objects.get(pk=pk)
        except ElectricActuatorRequirement.DoesNotExist:
            return Response(status=404)
        serializer = ElectricActuatorRequirementSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        try:
            item = ElectricActuatorRequirement.objects.get(pk=pk)
        except ElectricActuatorRequirement.DoesNotExist:
            return Response(status=404)
        item.delete()
        return Response(status=204)


class ElectricActuatorRequirementAPIListView(APIView):

    def get(self, request):
        items = ElectricActuatorRequirement.objects.order_by('pk')
        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(items, request)
        serializer = ElectricActuatorRequirementSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = ElectricActuatorRequirementSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


# class ValveRequirementAPIView(APIView):
#
#     def get(self, request, pk):
#         try:
#             item = ValveRequirement.objects.get(pk=pk)
#             serializer = ValveRequirementSerializer(item)
#             return Response(serializer.data)
#         except ValveRequirement.DoesNotExist:
#             return Response(status=404)
#
#     def put(self, request, pk):
#         try:
#             item = ValveRequirement.objects.get(pk=pk)
#         except ValveRequirement.DoesNotExist:
#             return Response(status=404)
#         serializer = ValveRequirementSerializer(item, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=400)
#
#     def delete(self, request, pk):
#         try:
#             item = ValveRequirement.objects.get(pk=pk)
#         except ValveRequirement.DoesNotExist:
#             return Response(status=404)
#         item.delete()
#         return Response(status=204)
#
#
# class ValveRequirementAPIListView(APIView):
#
#     def get(self, request):
#         items = ValveRequirement.objects.order_by('pk')
#         paginator = PageNumberPagination()
#         result_page = paginator.paginate_queryset(items, request)
#         serializer = ValveRequirementSerializer(result_page, many=True)
#         return paginator.get_paginated_response(serializer.data)
#
#     def post(self, request):
#         serializer = ValveRequirementSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=201)
#         return Response(serializer.errors, status=400)
#

class RequestItemHandler:
    """
    Класс, объединяющий логику сериализации и обработки запросов.
    """

    # @staticmethod
    # def get_valve_requirement(obj):
    #     """
    #     Получает сериализованные данные для ValveRequirement.
    #     """
    #     try:
    #         valve_requirement = obj.valve_requirement_for_request_line
    #         return {
    #             'id': valve_requirement.id,
    #             'valve_model_model_line_str': valve_requirement.valve_model_model_line_str,
    #         }
    #     except ValveRequirement.DoesNotExist:
    #         return None

    @staticmethod
    def get_electric_actuator_requirement(obj):
        """
        Получает сериализованные данные для ElectricActuatorRequirement.
        """
        try:
            electric_actuator_requirement = obj.electric_actuator_requirement_for_request_line
            return {
                'id': electric_actuator_requirement.id,
            }
        except ElectricActuatorRequirement.DoesNotExist:
            return None

    @staticmethod
    def serialize_client_request_item(item):
        """
        Сериализует ClientRequestItem с его связанными объектами.
        """
        return {
            'id': item.id,
            'item_no': item.item_no,
            'request_line_number': item.request_line_number,
            'request_line_ol': item.request_line_ol,
            'valve_requirement': RequestItemHandler.get_valve_requirement(item),
            'electric_actuator_requirement': RequestItemHandler.get_electric_actuator_requirement(item),
        }

    @staticmethod
    def validate_request_parent(request_parent):
        """
        Проверяет, что request_parent существует.
        """
        if not ClientRequests.objects.filter(pk=request_parent).exists():
            raise serializers.ValidationError("ClientRequest с таким ID не существует.")
        return request_parent

    @staticmethod
    def get_request_items(request_parent):
        """
        Возвращает список сериализованных ClientRequestItem для указанного request_parent.
        """
        items = ClientRequestItem.objects.filter(request_parent=request_parent)
        return [RequestItemHandler.serialize_client_request_item(item) for item in items]


#
#
#
  # path('client-request-lines-list/',ClientRequestItemAPIView.as_view()), #Получение списка строк по id запроса клиента
  #
  #
class ClientRequestItemView(APIView):
    """
    Вьюха, которая использует RequestItemHandler для обработки запросов.
    """

    def get(self, request, *args, **kwargs):
        request_parent = request.query_params.get('request_parent')
        if not request_parent:
            return Response(
                {"error": "Параметр request_parent обязателен."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            request_parent = int(request_parent)
            RequestItemHandler.validate_request_parent(request_parent)
            items = RequestItemHandler.get_request_items(request_parent)
            return Response(items, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
