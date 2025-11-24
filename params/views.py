# # views.py
# from rest_framework import generics, viewsets
#
#
# from .models import PowerSupplies, ExdOption, IpOption, BodyCoatingOption, BlinkerOption, SwitchesParameters, \
#     EnvTempParameters, DigitalProtocolsSupportOption, ControlUnitInstalledOption, ActuatorGearboxOutputType, \
#     ValveTypes, HandWheelInstalledOption, OperatingModeOption, ActuatorGearBoxCombinationTypes, MountingPlateTypes, \
#     StemShapes, StemSize, ThreadTypes, MeasureUnits, ThreadSize, CertVariety, CertData,\
#     MechanicalIndicatorInstalledOption, SafetyPositionOption
#
# from .serializers import PowerSuppliesSerializer, ExdOptionSerializer, IpOptionSerializer, \
#     BodyCoatingOptionSerializer, BlinkerOptionSerializer, SwitchesParametersSerializer, EnvTempParametersSerializer, \
#     DigitalProtocolsSupportOptionSerializer, ControlUnitInstalledOptionSerializer, \
#     ActuatorGearboxOutputTypeTypeSerializer, ValveTypesSerializer, \
#     HandWheelInstalledOptionSerializer, OperatingModeOptionOptionSerializer, ActuatorGearBoxCombinationTypesSerializer, \
#     ThreadSizeSerializer, MeasureUnitsSerializer, ThreadTypesSerializer, StemSizeSerializer, StemShapesSerializer, \
#     MountingPlateTypesSerializer, \
#     MechanicalIndicatorInstalledOptionSerializer, SafetyPositionOptionSerializer, CertVarietySerializer, \
#     CertDataSerializer
#
#
# class SafetyPositionOptionViewSet(viewsets.ModelViewSet):
#     queryset = SafetyPositionOption.objects.all()
#     serializer_class = SafetyPositionOptionSerializer
#
# class ThreadTypesViewSet(viewsets.ModelViewSet):
#     queryset = ThreadTypes.objects.all()
#     serializer_class = ThreadTypesSerializer
#
#
# class StemSizeViewSet(viewsets.ModelViewSet):
#     queryset = StemSize.objects.all()
#     serializer_class = StemSizeSerializer
#
#
# class StemShapesViewSet(viewsets.ModelViewSet):
#     queryset = StemShapes.objects.all()
#     serializer_class = StemShapesSerializer
#
#
# class ThreadSizeViewSet(viewsets.ModelViewSet):
#     queryset = ThreadSize.objects.all()
#     serializer_class = ThreadSizeSerializer
#
#
# class MeasureUnitsViewSet(viewsets.ModelViewSet):
#     serializer_class = MeasureUnitsSerializer
#
#     def get_queryset(self):
#         queryset = MeasureUnits.objects.all()
#         measure_type = self.request.query_params.get('measure_type')
#         if measure_type:
#             queryset = queryset.filter(measure_type=measure_type)
#         return queryset
#
# class MountingPlateTypesViewSet(viewsets.ModelViewSet):
#     queryset = MountingPlateTypes.objects.all()
#     serializer_class = MountingPlateTypesSerializer
#
#
# class MountingPlateTypesListView(generics.ListAPIView):
#     queryset = MountingPlateTypes.objects.all()
#     serializer_class = MountingPlateTypesSerializer
#
#
# class ActuatorGearBoxCombinationTypesViewSet(viewsets.ModelViewSet):
#     queryset = ActuatorGearBoxCombinationTypes.objects.all()
#     serializer_class = ActuatorGearBoxCombinationTypesSerializer
#
#
# class ExdOptionViewSet(viewsets.ModelViewSet):
#     queryset = ExdOption.objects.all()
#     serializer_class = ExdOptionSerializer
#
#
# class MechanicalIndicatorInstalledOptionViewSet(viewsets.ModelViewSet):
#     queryset = MechanicalIndicatorInstalledOption.objects.all()
#     serializer_class = MechanicalIndicatorInstalledOptionSerializer
#
#
# class IpOptionViewSet(viewsets.ModelViewSet):
#     queryset = IpOption.objects.all()
#     serializer_class = IpOptionSerializer
#     ordering = ['ip_rank']
#     list_display = ('symbolic_code', 'ip_rank', 'text_description')
#
#
# class OperatingModeOptionViewSet(viewsets.ModelViewSet):
#     queryset = OperatingModeOption.objects.all()
#     serializer_class = OperatingModeOptionOptionSerializer
#
#
# class HandWheelInstalledOptionViewSet(viewsets.ModelViewSet):
#     queryset = HandWheelInstalledOption.objects.all()
#     serializer_class = HandWheelInstalledOptionSerializer
#
#
# class ValveTypesViewSet(viewsets.ModelViewSet):
#     queryset = ValveTypes.objects.all()
#     serializer_class = ValveTypesSerializer
#
#
# class ActuatorGearboxOutputTypeViewSet(viewsets.ModelViewSet):
#     queryset = ActuatorGearboxOutputType.objects.all()
#     serializer_class = ActuatorGearboxOutputTypeTypeSerializer
#
#
# class ControlUnitInstalledOptionOptionViewSet(viewsets.ModelViewSet):
#     queryset = ControlUnitInstalledOption.objects.all()
#     serializer_class = ControlUnitInstalledOptionSerializer
#
#
# class DigitalProtocolsSupportOptionViewSet(viewsets.ModelViewSet):
#     queryset = DigitalProtocolsSupportOption.objects.all()
#     serializer_class = DigitalProtocolsSupportOptionSerializer
#
#
# class BodyCoatingOptionViewSet(viewsets.ModelViewSet):
#     queryset = BodyCoatingOption.objects.all()
#     serializer_class = BodyCoatingOptionSerializer
#
#
# class EnvTempParametersViewSet(viewsets.ModelViewSet):
#     queryset = EnvTempParameters.objects.all()
#     serializer_class = EnvTempParametersSerializer
#
#
# class SwitchesParametersViewSet(viewsets.ModelViewSet):
#     queryset = SwitchesParameters.objects.all()
#     serializer_class = SwitchesParametersSerializer
#
#
# class BlinkerOptionViewSet(viewsets.ModelViewSet):
#     queryset = BlinkerOption.objects.all()
#     serializer_class = BlinkerOptionSerializer
#
#
# class PowerSuppliesViewSet(viewsets.ModelViewSet):
#     queryset = PowerSupplies.objects.all()
#     serializer_class = PowerSuppliesSerializer
#
#
# class CertVarietyViewSet(viewsets.ModelViewSet):
#     queryset = CertVariety.objects.all()
#     serializer_class = CertVarietySerializer
#
#
# class CertDataViewSet(viewsets.ModelViewSet):
#     queryset = CertData.objects.all()
#     serializer_class = CertDataSerializer
