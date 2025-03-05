from django.shortcuts import render
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound


class GetUrlByNameAPIView(APIView):
    def get(self, request, name):
        try:
            url = reverse(name)
            return Response({"url": url})
        except Exception as e:
            raise NotFound(f"URL для имени {name} не найден: {str(e)}. Запрос:{request}, Name:{name}")


def index(request):
    return render(request, '../data_processor/templates/index.html')
