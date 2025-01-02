# views.py
from rest_framework import viewsets
from .models import ElectroModel, ElectroIPChoiceModel
from .serializers import ElectroModelSerializer, ElectroIPChoiceSerializer


class IPChoiceViewSet(viewsets.ModelViewSet):
    queryset = ElectroIPChoiceModel.objects.all()
    serializer_class = ElectroIPChoiceSerializer


class ElectroModelViewSet(viewsets.ModelViewSet):
    queryset = ElectroModel.objects.all()
    serializer_class = ElectroModelSerializer
