# views.py
from rest_framework import viewsets
from .models import PowerSupplies, ExdOption, IpOption, BodyCoatingOption, BlinkerOption, SwitchesParameters, \
    EnvTempParameters, DigitalProtocolsSupportOption, ControlUnitInstalledOption, ActuatorGearboxOutputType, \
    ValveTypes, HandWheelInstalledOption, OperatingModeOption, ActuatorGearBoxCombinationTypes
from .serializers import PowerSuppliesSerializer, ExdOptionSerializer, IpOptionSerializer, \
    BodyCoatingOptionSerializer, BlinkerOptionSerializer, SwitchesParametersSerializer, EnvTempParametersSerializer, \
    DigitalProtocolsSupportOptionSerializer, ControlUnitInstalledOptionSerializer, \
    ActuatorGearboxOutputTypeTypeSerializer, ValveTypesSerializer, \
    HandWheelInstalledOptionSerializer, OperatingModeOptionOptionSerializer, ActuatorGearBoxCombinationTypesSerializer


class ActuatorGearBoxCombinationTypesViewSet(viewsets.ModelViewSet):
    queryset = ActuatorGearBoxCombinationTypes.objects.all()
    serializer_class = ActuatorGearBoxCombinationTypesSerializer


class ExdOptionViewSet(viewsets.ModelViewSet):
    queryset = ExdOption.objects.all()
    serializer_class = ExdOptionSerializer


class IpOptionViewSet(viewsets.ModelViewSet):
    queryset = IpOption.objects.all()
    serializer_class = IpOptionSerializer


class OperatingModeOptionViewSet(viewsets.ModelViewSet):
    queryset = OperatingModeOption.objects.all()
    serializer_class = OperatingModeOptionOptionSerializer


class HandWheelInstalledOptionViewSet(viewsets.ModelViewSet):
    queryset = HandWheelInstalledOption.objects.all()
    serializer_class = HandWheelInstalledOptionSerializer


class GearBoxTypesViewSet(viewsets.ModelViewSet):
    queryset = GearBoxTypes.objects.all()
    serializer_class = GearBoxTypesSerializer


class ValveTypesViewSet(viewsets.ModelViewSet):
    queryset = ValveTypes.objects.all()
    serializer_class = ValveTypesSerializer


class ActuatorGearboxOutputTypeViewSet(viewsets.ModelViewSet):
    queryset = ActuatorGearboxOutputType.objects.all()
    serializer_class = ActuatorGearboxOutputTypeTypeSerializer


class ControlUnitInstalledOptionOptionViewSet(viewsets.ModelViewSet):
    queryset = ControlUnitInstalledOption.objects.all()
    serializer_class = ControlUnitInstalledOptionSerializer


class DigitalProtocolsSupportOptionViewSet(viewsets.ModelViewSet):
    queryset = DigitalProtocolsSupportOption.objects.all()
    serializer_class = DigitalProtocolsSupportOptionSerializer


class BodyCoatingOptionViewSet(viewsets.ModelViewSet):
    queryset = BodyCoatingOption.objects.all()
    serializer_class = BodyCoatingOptionSerializer


class EnvTempParametersViewSet(viewsets.ModelViewSet):
    queryset = EnvTempParameters.objects.all()
    serializer_class = EnvTempParametersSerializer


class SwitchesParametersViewSet(viewsets.ModelViewSet):
    queryset = SwitchesParameters.objects.all()
    serializer_class = SwitchesParametersSerializer


class BlinkerOptionViewSet(viewsets.ModelViewSet):
    queryset = BlinkerOption.objects.all()
    serializer_class = BlinkerOptionSerializer


class PowerSuppliesViewSet(viewsets.ModelViewSet):
    queryset = PowerSupplies.objects.all()
    serializer_class = PowerSuppliesSerializer
