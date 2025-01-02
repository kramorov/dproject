# serializers.py
from rest_framework import serializers
from .models import PowerSupplies, ExdOption, IpOption, BodyCoatingOption, BlinkerOption, SwitchesParameters, \
    EnvTempParameters, DigitalProtocolsSupportOption, ControlUnitInstalledOption, ActuatorGearboxOutputType,\
    ValveTypes, HandWheelInstalledOption, OperatingModeOption, ActuatorGearBoxCombinationTypes


# PowerSuppliesSerializer, ExdOptionSerializer, IpOptionSerializer, BodyCoatingOptionSerializer, \
# BlinkerOptionSerializer, SwitchesParametersSerializer, EnvTempParametersSerializer \
# DigitalProtocolsSupportOptionSerializer, ControlUnitInstalledOptionSerializer, ActuatorGearboxOutputTypeTypeSerializer, \
# ValveTypesSerializer, GearBoxTypesSerializer, HandWheelInstalledOptionSerializer, \
# OperatingModeOptionOptionSerializer, ActuatorGearBoxCombinationTypesSerializer


class ActuatorGearBoxCombinationTypesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActuatorGearBoxCombinationTypes
        fields = ['id', 'symbolic_code', 'electric_actuator_type', 'gearbox_type',
                  'pneumatic_actuator_type', 'text_description']


class PowerSuppliesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PowerSupplies
        fields = ['id', 'symbolic_code', 'voltage_value', 'voltage_type', 'text_description']


class ExdOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExdOption
        fields = ['id', 'symbolic_code', 'exd_full_code', 'text_description']


class IpOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = IpOption
        fields = ['id', 'symbolic_code', 'ip_rank', 'text_description']


class BodyCoatingOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BodyCoatingOption
        fields = ['id', 'symbolic_code', 'text_description']


class BlinkerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlinkerOption
        fields = ['id', 'symbolic_code', 'text_description']


class SwitchesParametersSerializer(serializers.ModelSerializer):
    class Meta:
        model = SwitchesParameters
        fields = ['id', 'symbolic_code', 'text_description']


class EnvTempParametersSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnvTempParameters
        fields = ['id', 'symbolic_code', 'min_temp', 'max_temp', 'text_description']


class DigitalProtocolsSupportOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DigitalProtocolsSupportOption
        fields = ['id', 'symbolic_code', 'text_description']


class ControlUnitInstalledOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControlUnitInstalledOption
        fields = ['id', 'symbolic_code', 'text_description']


class ActuatorGearboxOutputTypeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActuatorGearboxOutputType
        fields = ['id', 'symbolic_code', 'text_description']


class ValveTypesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValveTypes
        fields = ['id', 'symbolic_code', 'actuator_gearbox_combinations','text_description']


class HandWheelInstalledOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HandWheelInstalledOption
        fields = ['id', 'symbolic_code', 'text_description']


class OperatingModeOptionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperatingModeOption
        fields = ['id', 'symbolic_code', 'text_description']
