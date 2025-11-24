# # myapp/urls.py
# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
#
#
# from .views import OperatingModeOptionViewSet, HandWheelInstalledOptionViewSet, IpOptionViewSet, \
#     ValveTypesViewSet, ActuatorGearboxOutputTypeViewSet, ControlUnitInstalledOptionOptionViewSet, \
#     DigitalProtocolsSupportOptionViewSet, BodyCoatingOptionViewSet, EnvTempParametersViewSet, \
#     SwitchesParametersViewSet, BlinkerOptionViewSet, PowerSuppliesViewSet, ActuatorGearBoxCombinationTypesViewSet, \
#     ThreadTypesViewSet, StemSizeViewSet, StemShapesViewSet, ThreadSizeViewSet, MeasureUnitsViewSet, \
#     CertVarietyViewSet, CertDataViewSet, MountingPlateTypesViewSet, ExdOptionViewSet, CertVarietyViewSet, \
#     CertDataViewSet
# from .views import MountingPlateTypesListView
#
# router = DefaultRouter()
# router.register(r'actuator-gearbox-combinations', ActuatorGearBoxCombinationTypesViewSet,
#                 basename='actuatorgearboxcombinationtypes')
# router.register(r'op-modes', OperatingModeOptionViewSet)
# router.register(r'ip-options', IpOptionViewSet)
# router.register(r'exd-options', ExdOptionViewSet)
# router.register(r'hand-wheel', HandWheelInstalledOptionViewSet)
# router.register(r'valve-types', ValveTypesViewSet)
# router.register(r'actuator-gearboxes-types', ActuatorGearboxOutputTypeViewSet)
# router.register(r'cu-installed', ControlUnitInstalledOptionOptionViewSet)
# router.register(r'digital-protocols', DigitalProtocolsSupportOptionViewSet)
# router.register(r'body-coatings', BodyCoatingOptionViewSet)
# router.register(r'env-temps', EnvTempParametersViewSet)
# router.register(r'switches-types', SwitchesParametersViewSet)
# router.register(r'blinker-options', BlinkerOptionViewSet)
# router.register(r'thread-types', ThreadTypesViewSet)
# router.register(r'stem-size-types', StemSizeViewSet)
# router.register(r'stem-shapes-types', StemShapesViewSet)
# router.register(r'thread-size-types', ThreadSizeViewSet)
# router.register(r'measure-units-types', MeasureUnitsViewSet, basename='measure-units-types')
# router.register(r'mounting-plate-types', MountingPlateTypesViewSet)
# router.register(r'power-types', PowerSuppliesViewSet)
# router.register(r'certificate-types', CertVarietyViewSet)
# router.register(r'certificate-data', CertDataViewSet)
#
# # list_url_patterns = [
# #     path('api/params/mounting-plate-types/list/', MountingPlateTypesListView.as_view(), name='mounting-plate-types-list'),
# # ]
# # console.log(router.urls)
# urlpatterns = [
#     path('mounting-plate-types/list', MountingPlateTypesListView.as_view(), name='mounting-plate-types-list'),
#     path('', include(router.urls)),
#
#     # name='mounting-plate-types-list' ----- >  <div class="mounting-plate-types">
# ]
#
# # urlpatterns.extend(list_url_patterns)