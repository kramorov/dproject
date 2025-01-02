# views.py
from rest_framework import viewsets
from .models import MyModel, IPChoice, TempChoice
from .serializers import MyModelSerializer, IPChoiceSerializer, TempChoiceSerializer

class IPChoiceViewSet(viewsets.ModelViewSet):
    queryset = IPChoice.objects.all()
    serializer_class = IPChoiceSerializer

class TempChoiceViewSet(viewsets.ModelViewSet):
    queryset = TempChoice.objects.all()
    serializer_class = TempChoiceSerializer

class MyModelViewSet(viewsets.ModelViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
