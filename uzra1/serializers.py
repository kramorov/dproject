# serializers.py
from rest_framework import serializers
from .models import MyModel, IPChoice, TempChoice


class IPChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = IPChoice
        fields = ['id', 'ip_value']

class TempChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempChoice
        fields = ['id', 'temp_value', 'min', 'max']

class MyModelSerializer(serializers.ModelSerializer):
    ip = IPChoiceSerializer()
    temp = TempChoiceSerializer()

    class Meta:
        model = MyModel
        fields = ['id', 'ip', 'temp', 'torque']
