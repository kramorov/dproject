from rest_framework import serializers

from .models import Brands, Producer


class BrandsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brands
        fields = ['id', 'name']


class ProducerSerializer(serializers.ModelSerializer):
    brands = BrandsSerializer(many=True)

    class Meta:
        model = Producer
        fields = ['id', 'organization', 'brands']
