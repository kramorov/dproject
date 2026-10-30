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
router.register('control-signal-forms', api.CuControlSignalFormViewSet,
                basename='cu-ctl-form')
router.register('feedback-signal-forms', api.CuFeedbackSignalFormViewSet,
                basename='cu-fb-form')
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
router.register('feedback-device-kinds', api.EaFeedbackDeviceKindViewSet,
                basename='cu-device-kind')
router.register('feedback-technologies', api.EaFeedbackTechnologyViewSet,
                basename='cu-device-technology')
router.register('control-unit-kinds', api.ControlUnitKindViewSet,
                basename='cu-kind')
router.register('signal-form-categories', api.EaSignalFormCategoryViewSet,
                basename='cu-form-category')
router.register('control-signal-roles', api.EaControlSignalRoleViewSet,
                basename='cu-control-role')
router.register('feedback-signal-roles', api.EaFeedbackSignalRoleViewSet,
                basename='cu-feedback-role')
router.register('contact-normals', api.EaContactNormalViewSet,
                basename='cu-contact-normal')
router.register('protocol-transports', api.EaProtocolTransportViewSet,
                basename='cu-transport')
router.register('polarities', api.CuPolarityViewSet, basename='cu-polarity')

urlpatterns = [
    path('units/', api.units_view, name='cu_units'),
    path('meta/', api.meta_view, name='cu_meta'),
    path('series-units/', api.series_units_view, name='cu_series_units'),
    path('describe/', api.describe_view, name='cu_describe'),
    path('package/', api.package_view, name='cu_package'),
    path('unit-matrix/', api.unit_matrix_view, name='cu_unit_matrix'),
    path('unit-matrix/save/', api.unit_matrix_save_view, name='cu_unit_matrix_save'),
    *router.urls,
]
