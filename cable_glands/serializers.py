# serializers.py
from rest_framework import serializers
from .models import CableGlandModelLine, CableGlandItem, \
    CableGlandItemType, CableGlandBodyMaterial
from params.serializers import ActuatorGearboxOutputTypeTypeSerializer, IpOptionSerializer, \
    BodyCoatingOptionSerializer, ExdOptionSerializer, BlinkerOptionSerializer, SwitchesParametersSerializer, \
    EnvTempParametersSerializer, DigitalProtocolsSupportOptionSerializer, ControlUnitInstalledOptionSerializer, \
    HandWheelInstalledOptionSerializer, OperatingModeOptionOptionSerializer
from producers.serializers import BrandsSerializer, ProducerSerializer


class CableGlandBodyMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = CableGlandBodyMaterial
        fields = ['id', 'name', 'text_description']


class CableGlandItemTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CableGlandItemType
        fields = ['id', 'name', 'text_description']


class CableGlandItemSerializer(serializers.ModelSerializer):
    # Сериализатор для поля thread, чтобы выводить информацию о резьбе
    thread_a = serializers.StringRelatedField()  # Покажет строковое представление модели ThreadSize
    thread_b = serializers.StringRelatedField()  # Покажет строковое представление модели ThreadSize

    class Meta:
        model = CableGlandItem
        fields = ['id', 'name', 'model_line', 'thread_a', 'thread_b', 'temp_min', 'temp_max', 'cable_diameter_inner_min', \
                  'cable_diameter_inner_max', 'cable_diameter_outer_min', 'cable_diameter_outer_max', \
                  'dn_metal_sleeve', 'parent']
        depth = 3  # Ограничиваем глубину вложенности


class CableGlandModelLineSerializer(serializers.ModelSerializer):
    # producer = serializers.StringRelatedField()  # Покажет строковое представление модели
    cable_gland_type = serializers.StringRelatedField()  # Покажет строковое представление модели

    class Meta:
        model = CableGlandModelLine
        fields = ['id', 'symbolic_code', 'brand', 'cable_gland_type', 'ip', 'exd', 'for_armored_cable', \
                  'for_metal_sleeve_cable', 'for_pipelines_cable', 'thread_external', \
                  'thread_internal', 'temp_min', 'temp_max', 'gost', 'text_description']
