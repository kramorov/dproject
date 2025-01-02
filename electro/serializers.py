# serializers.py
from rest_framework import serializers
from .models import ElectroModel, ElectroIPChoiceModel


class ElectroIPChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectroIPChoiceModel
        fields = ['id', 'ip_value']


class ElectroModelSerializer(serializers.ModelSerializer):
    ip = ElectroIPChoiceSerializer()

    class Meta:
        model = ElectroModel
        fields = ['id', 'ip', 'temp', 'torque']
