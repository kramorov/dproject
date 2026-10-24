# ea_control/urls.py
"""URL API ea_control (под префиксом /api/ea-control/)."""
from django.urls import path
from rest_framework.routers import DefaultRouter

from ea_control import api

router = DefaultRouter()
router.register('control-units', api.ControlUnitViewSet, basename='cu-control-unit')
router.register('sections', api.CuSectionNodeViewSet, basename='cu-section')
router.register('slots', api.CuSlotViewSet, basename='cu-slot')
router.register('slot-options', api.CuSlotOptionViewSet, basename='cu-slot-option')
router.register('matrix-entries', api.CuMatrixEntryViewSet, basename='cu-matrix')
router.register('slot-rules', api.CuSlotRuleViewSet, basename='cu-rule')
router.register('signal-forms', api.CuSignalFormViewSet, basename='cu-form')
router.register('control-signals', api.CuControlSignalViewSet, basename='cu-ctl')
router.register('feedback-signals', api.CuFeedbackSignalViewSet, basename='cu-fb')
router.register('comm-protocols', api.CuCommProtocolViewSet, basename='cu-proto')
router.register('feedback-devices', api.CuFeedbackDeviceViewSet, basename='cu-device')
router.register('heater-supplies', api.CuHeaterSupplyViewSet, basename='cu-heater')
router.register('location-options', api.CuLocationOptionViewSet, basename='cu-location')
router.register('capabilities', api.CuCapabilityViewSet, basename='cu-capability')
router.register('local-control-types', api.CuLocalControlTypeViewSet,
                basename='cu-local-ctl')
router.register('display-types', api.CuDisplayTypeViewSet, basename='cu-display')
router.register('unit-power-sources', api.CuUnitPowerSourceViewSet,
                basename='cu-unit-power')
router.register('signal-power-sources', api.CuSignalPowerSourceViewSet,
                basename='cu-sp-source')
router.register('signal-powers', api.CuSignalPowerViewSet, basename='cu-sp')
router.register('control-logics', api.CuControlLogicViewSet, basename='cu-logic')
router.register('signal-types', api.CuSignalTypeViewSet, basename='cu-stype')

urlpatterns = [
    path('units/', api.units_view, name='cu_units'),
    path('meta/', api.meta_view, name='cu_meta'),
    path('series-units/', api.series_units_view, name='cu_series_units'),
    path('describe/', api.describe_view, name='cu_describe'),
    path('package/', api.package_view, name='cu_package'),
    *router.urls,
]
