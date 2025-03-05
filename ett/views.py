from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import render

from .models import EttDocument
from .serializers import EttDocumentSerializer, EttStringSerializer

class EttDocumentViewSet(viewsets.ModelViewSet):
    queryset = EttDocument.objects.all()  # Получение всех объектов EttDocument
    serializer_class = EttDocumentSerializer  # Указание сериализатора


class EttStringView(APIView) :
    def post(self , request , *args , **kwargs) :
        try :
            # Получаем строку из данных запроса
            input_string = request.data.get('input_string' , '')

            # Создаем экземпляр сериализатора с переданными данными и проверяем строку
            serializer = EttStringSerializer(data={'input_string' : input_string})

            # Валидация данных с автоматическим вызовом `to_internal_value()`
            if serializer.is_valid() :
                # Преобразование данных в формат для ответа с вызовом `to_representation()`
                # Возвращаем разобранные данные
                return Response(serializer.data , status=status.HTTP_200_OK)

            # Если данные не валидны, возвращаем ошибку
            return Response(serializer.errors , status=status.HTTP_400_BAD_REQUEST)

        except Exception as e :
            # Логируем ошибку
            print('Error:' , e)
            # Возвращаем ошибку серверного типа
            return Response({'detail' : str(e)} , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

