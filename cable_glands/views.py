# views.py
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.decorators import action

from .models import CableGlandModelLine, CableGlandBodyMaterial, CableGlandItemType, \
    CableGlandItem
from .serializers import CableGlandModelLineSerializer, CableGlandItemSerializer, CableGlandBodyMaterialSerializer,\
    CableGlandItemTypeSerializer


class CableGlandBodyMaterialViewSet(viewsets.ModelViewSet):
    queryset = CableGlandBodyMaterial.objects.all()
    serializer_class = CableGlandBodyMaterialSerializer


class CableGlandItemViewSet(viewsets.ModelViewSet):
    queryset = CableGlandItem.objects.all()
    serializer_class = CableGlandItemSerializer


class CableGlandModelLineViewSet(viewsets.ModelViewSet):
    queryset = CableGlandModelLine.objects.all()
    serializer_class = CableGlandModelLineSerializer


class CableGlandItemTypeViewSet(viewsets.ModelViewSet):
    queryset = CableGlandItemType.objects.all()
    serializer_class = CableGlandItemTypeSerializer

