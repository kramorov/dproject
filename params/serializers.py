# serializers.py
from rest_framework import serializers
from .models import PowerSupplies, ExdOption, IpOption, BodyCoatingOption, BlinkerOption, SwitchesParameters, \
    EnvTempParameters, DigitalProtocolsSupportOption, ControlUnitInstalledOption, ActuatorGearboxOutputType, \
    ValveTypes, HandWheelInstalledOption, OperatingModeOption, ActuatorGearBoxCombinationTypes, MountingPlateTypes, \
    StemShapes, StemSize, ThreadTypes, MeasureUnits, ThreadSize, Certificate, CertificateType, \
    MechanicalIndicatorInstalledOption, SafetyPositionOption, ControlUnitTypeOption, ControlUnitLocationOption


# PowerSuppliesSerializer, ExdOptionSerializer, IpOptionSerializer, BodyCoatingOptionSerializer,
# \ BlinkerOptionSerializer, SwitchesParametersSerializer, EnvTempParametersSerializer \
# DigitalProtocolsSupportOptionSerializer, ControlUnitInstalledOptionSerializer,
# ActuatorGearboxOutputTypeTypeSerializer, \ ValveTypesSerializer, GearBoxTypesSerializer,
# HandWheelInstalledOptionSerializer, \ OperatingModeOptionOptionSerializer, ActuatorGearBoxCombinationTypesSerializer


class ControlUnitTypeOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControlUnitTypeOption
        fields = ['id', 'symbolic_code', 'text_description']

class ControlUnitLocationOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControlUnitLocationOption
        fields = ['id', 'symbolic_code', 'text_description']

class SafetyPositionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyPositionOption
        fields = ['id', 'symbolic_code', 'text_description']

class ThreadSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThreadSize
        fields = ['id', 'symbolic_code', 'text_description', 'thread_type', 'thread_diameter', 'thread_pitch', \
                  'measure_units']


class MeasureUnitsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasureUnits
        fields = ['id', 'symbolic_code', 'text_description', 'symbolic_description']


class ThreadTypesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThreadTypes
        fields = ['id', 'symbolic_code', 'text_description']


class StemSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StemSize
        fields = ['id', 'symbolic_code', 'text_description','stem_type', 'stem_diameter', 'chunk_x', 'chunk_y',\
                  'chunk_z', 'thread_pitch']


class StemShapesSerializer(serializers.ModelSerializer):
    class Meta:
        model = StemShapes
        fields = ['id', 'symbolic_code', 'text_description']


class MountingPlateTypesSerializer(serializers.ModelSerializer):
    class Meta:
        model = MountingPlateTypes
        fields = ['id', 'symbolic_code']


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

class MechanicalIndicatorInstalledOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExdOption
        fields = ['id', 'symbolic_code',  'text_description']


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
        fields = ['id', 'symbolic_code', 'actuator_gearbox_combinations', 'text_description']


class HandWheelInstalledOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HandWheelInstalledOption
        fields = ['id', 'symbolic_code', 'text_description']


class OperatingModeOptionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperatingModeOption
        fields = ['id', 'symbolic_code', 'text_description']


class CertificateTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificateType
        fields = ['symbolic_code', 'text_description']


class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = ['certificate_type', 'symbolic_code', 'text_description', 'valid_from','valid_until']

