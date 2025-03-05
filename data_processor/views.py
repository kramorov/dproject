# data_processor/views.py
import sys

from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .processor import process_model_name

from .serializers import TextInputSerializer, ETTSerializer


class ETTView(APIView):
    def post(self, request, *args, **kwargs):
        # Получаем строку из данных запроса
        try :
            input_string = request.data.get('input_string', '')
            # # Получаем JSON из тела запроса
            # data = json.loads(request.body)
            # print('Received data:' , input_string)

            # # Создаем экземпляр сериализатора с переданными данными и проверяем строку
            serializer = ETTSerializer(data={'input_string': input_string})
            # Валидация данных с автоматическим вызовом `to_internal_value()`
            if serializer.is_valid():
                # Преобразование данных в формат для ответа с вызовом `to_representation()`
                # Возвращаем разобранные данные
                return Response(serializer.data, status=status.HTTP_200_OK)
            # Преобразование данных в формат для ответа с вызовом `to_representation()`
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e :
            print('Error:' , e)
            return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StringProcessorView(APIView):
    """API View to process strings."""

    @action(detail=False, methods=['post'])
    def post(self, request, *args, **kwargs):
        input_text = request.data.get('text', '')
        return Response({"result": input_text}, status=status.HTTP_200_OK)
        if not isinstance(input_text, str):
            return Response({"error": "Invalid input. Expected a string."}, status=status.HTTP_400_BAD_REQUEST)
        result_table = process_model_name(input_text)
        # lines = input_text.split('.')
        # # lines = [line.strip() for line in lines if line.strip()]  # Удалим пустые строки
        # result_table = [{"original": input_text, "split": substring.strip()} for substring in lines if substring.strip()]
        return Response({"result": result_table}, status=status.HTTP_200_OK)
        # return Response({"result": lines}, status=status.HTTP_200_OK)

class TextInputViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], )
    def process_text(self, request):
        print(request.data)
        return Response('Пустой ответ')
        serializer = TextInputSerializer(data=request.data)
        sys.stderr.write('Test')
        if serializer.is_valid():
            input_text = serializer.validated_data['input_text']
            # Разделим строку по точке
            lines = input_text.split('.')
            lines = [line.strip() for line in lines if line.strip()]  # Удалим пустые строки
            return Response(lines)
        else:
            return Response('Пустой ответ')  # Response(serializer.errors, status=400)


class IndexView(APIView):
    def get(self, request):
        # Рендерим шаблон главной страницы
        return render(request, 'text_processor/index.html')


class HelloView(APIView):
    def get(self, request):
        html_content = "<h1 style='text-align:center; color: blue;'>Hello!</h1>"
        return Response(html_content, content_type='text/html', status=status.HTTP_200_OK)
