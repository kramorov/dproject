# myapp/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OperatingModeOptionViewSet, HandWheelInstalledOptionViewSet, GearBoxTypesViewSet,\
    ValveTypesViewSet, ActuatorGearboxOutputTypeViewSet, ControlUnitInstalledOptionOptionViewSet,\
    DigitalProtocolsSupportOptionViewSet, BodyCoatingOptionViewSet, EnvTempParametersViewSet,\
    SwitchesParametersViewSet, BlinkerOptionViewSet, PowerSuppliesViewSet, ActuatorGearBoxCombinationTypesViewSet

router = DefaultRouter()
router.register(r'actuator-gearbox-combinations', ActuatorGearBoxCombinationTypesViewSet)
router.register(r'op-modes', OperatingModeOptionViewSet)
router.register(r'hand-wheel', HandWheelInstalledOptionViewSet)
router.register(r'gear-boxes', GearBoxTypesViewSet)
router.register(r'valve-types', ValveTypesViewSet)
router.register(r'actuator-gearboxes-types', ActuatorGearboxOutputTypeViewSet)
router.register(r'cu-installed', ControlUnitInstalledOptionOptionViewSet)
router.register(r'digital-protocols', DigitalProtocolsSupportOptionViewSet)
router.register(r'body-coatings', BodyCoatingOptionViewSet)
router.register(r'env-temps', EnvTempParametersViewSet)
router.register(r'switches-types', SwitchesParametersViewSet)
router.register(r'blinker-options', BlinkerOptionViewSet)
router.register(r'power-types', PowerSuppliesViewSet)


urlpatterns = [
    path('api/params', include(router.urls)),
]
