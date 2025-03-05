from rest_framework import serializers

from params.serializers import MeasureUnitsSerializer , StemSizeSerializer , MountingPlateTypesSerializer , \
    ValveTypesSerializer
from producers.serializers import BrandsSerializer , ProducerSerializer
from .models import ValveLine, ValveModelData


class ValveLineSerializer(serializers.ModelSerializer):
    valve_producer = ProducerSerializer(read_only=True)
    valve_brand = BrandsSerializer(read_only=True)
    valve_type = ValveTypesSerializer(read_only=True)
    class Meta:
        model = ValveLine
        fields = ['symbolic_code', 'valve_producer', 'valve_brand', 'valve_type']


class ValveModelDataSerializer(serializers.ModelSerializer):
    valve_model_model_line = ValveLineSerializer(read_only=True)
    valve_model_pn_measure_unit = MeasureUnitsSerializer(read_only=True)
    valve_model_pn_delta_measure_unit = MeasureUnitsSerializer(read_only=True)
    valve_model_stem_size = StemSizeSerializer(read_only=True)
    valve_model_mounting_plate = MountingPlateTypesSerializer(many=True , read_only=True)
    valve_type = ValveTypesSerializer(read_only=True)

    class Meta :
        model = ValveModelData
        fields = [
            'valve_model_model_line',
            'valve_model_dn' ,
            'valve_model_pn' ,
            'valve_model_pn_measure_unit' ,
            'valve_model_pn_delta' ,
            'valve_model_pn_delta_measure_unit' ,
            'valve_model_torque_to_open' ,
            'valve_model_torque_to_close' ,
            'valve_model_rotations_to_open' ,
            'valve_model_stem_size' ,
            'valve_model_mounting_plate' ,
            'valve_type' ,
            'valve_stem_retract_type' ,
        ]
    # Если вы хотите разрешить создание или обновление объектов через API, добавьте методы create и update в сериализатор:
    # def create(self, validated_data):
    #     # Логика для создания объекта
    #     return super().create(validated_data)
    #
    # def update(self, instance, validated_data):
    #     # Логика для обновления объекта
    #     return super().update(instance, validated_data)