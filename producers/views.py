from rest_framework import viewsets

from .models import Brands, Producer
from .serializers import BrandsSerializer, ProducerSerializer


class BrandsViewSet(viewsets.ModelViewSet):
    queryset = Brands.objects.all()
    serializer_class = BrandsSerializer


class ProducerViewSet(viewsets.ModelViewSet):
    queryset = Producer.objects.all()
    serializer_class = ProducerSerializer

