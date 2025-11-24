# # views.py
# from rest_framework import viewsets
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework.decorators import action
# from rest_framework import serializers
# from rest_framework import status
# from .models import ModelLine, ElectricActuatorData, CableGlandHolesSet, WiringDiagram, ActualActuator
# from .serializers import ModelLineSerializer, ElectricActuatorDataSerializer, CableGlandHolesSetSerializer, \
#     WiringDiagramSerializer, TextInputSerializer, ActualActuatorSerializer
#
# import logging
#
# # Создаем логгер
# logger = logging.getLogger(__name__)
#
#
# class ActualActuatorViewSet(viewsets.ModelViewSet):
#     queryset = ActualActuator.objects.all()
#     serializer_class = ActualActuatorSerializer
#
#
# class ActualActuatorAPIView(APIView):
#     # Метод для получения всех объектов
#     def get(self, request, pk=None):
#         if pk:
#             actuator = ActualActuator.objects.get(pk=pk)
#             serializer = ActualActuatorSerializer(actuator)
#             return Response(serializer.data)
#         actuators = ActualActuator.objects.all()
#         serializer = ActualActuatorSerializer(actuators, many=True)
#         return Response(serializer.data)
#
#     # Метод для создания нового объекта
#     def post(self, request):
#         serializer = ActualActuatorSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     # Метод для обновления существующего объекта
#     def put(self, request, pk):
#         try:
#             actuator = ActualActuator.objects.get(pk=pk)
#         except ActualActuator.DoesNotExist:
#             return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
#
#         serializer = ActualActuatorSerializer(actuator, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     # Метод для удаления объекта
#     def delete(self, request, pk):
#         try:
#             actuator = ActualActuator.objects.get(pk=pk)
#         except ActualActuator.DoesNotExist:
#             return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
#
#         actuator.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)
#
#     # Метод для копирования объекта
#     def post(self, request, pk=None):
#         logger.info('Вызван метод Copy ActualActuatorAPIView')  # Логируем информацию в консоль
#         try:
#             actuator = ActualActuator.objects.get(pk=pk)
#         except ActualActuator.DoesNotExist:
#             return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
#
#         # Копируем все поля из существующей записи
#         actuator_data = ActualActuatorSerializer(actuator).data
#         actuator_data.pop('id', None)  # Удаляем старый id, чтобы избежать конфликта
#
#         # Если нужно, можно добавить новые поля для уникальности
#         actuator_data['actual_model_name'] = actuator_data['actual_model_name'] + ' (копия)'
#
#         # Создаем новый экземпляр модели с копией данных
#         serializer = ActualActuatorSerializer(data=actuator_data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# # class ActualActuatorListView(APIView):
# #     def get(self, request):
# #         actuators = ActualActuator.objects.all()
# #         serializer = ActualActuatorSerializer(actuators, many=True)
# #         return Response(serializer.data)
#
#
# class CableGlandHolesSetViewSet(viewsets.ModelViewSet):
#     queryset = CableGlandHolesSet.objects.all()
#     serializer_class = CableGlandHolesSetSerializer
#
#
# class ModelLineViewSet(viewsets.ModelViewSet):
#     queryset = ModelLine.objects.all()
#     serializer_class = ModelLineSerializer
#
#
# class ElectricActuatorDataViewSet(viewsets.ModelViewSet):
#     queryset = ElectricActuatorData.objects.all()
#     serializer_class = ElectricActuatorDataSerializer
#
#     def get_queryset(self):
#         queryset = super().get_queryset()
#         model_line_id = self.request.query_params.get('model_line')
#         voltage = self.request.query_params.get('voltage')
#
#         if model_line_id and voltage:
#             queryset = queryset.filter(model_line_id=model_line_id, voltage=voltage)
#         elif model_line_id:
#             queryset = queryset.filter(model_line_id=model_line_id)
#         elif voltage:
#             queryset = queryset.filter(voltage=voltage)
#             # Добавление сортировки по полю 'name'
#         queryset = queryset.order_by('name')  # Сортировка по возрастанию (если нужно по убыванию, используйте '-name')
#
#         return queryset
#
#
#
# class WiringDiagramViewSet(viewsets.ModelViewSet):
#     queryset = WiringDiagram.objects.all()
#     serializer_class = WiringDiagramSerializer
#
#     @action(detail=True, methods=['get'])
#     def get_electric_actuators(self, request, pk=None):
#         wiring_diagram = self.get_object()
#         model_line = wiring_diagram.applies_to_model_line
#         electric_actuators = ElectricActuatorData.objects.filter(model_line=model_line)
#         serializer = ElectricActuatorDataSerializer(electric_actuators, many=True)
#         return Response(serializer.data)
#
#
# class TextInputViewSet(viewsets.ViewSet):
#
#     @action(detail=False, methods=['post'])
#     def process_text(self, request):
#         serializer = TextInputSerializer(data=request.data)
#
#         if serializer.is_valid():
#             input_text = serializer.validated_data['input_text']
#             # Разделим строку по точке
#             lines = input_text.split('.')
#             lines = [line.strip() for line in lines if line.strip()]  # Удалим пустые строки
#             return Response(lines)
#         else:
#             return Response(serializer.errors, status=400)
