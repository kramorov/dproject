# electric_actuators/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api.views import EAOptionAPIView
from .api.views_constructor import ConstructorViewSet
from .api.views_admin import EAPowerSupplyMatrixView, EAPowerSupplyMatrixExportView, EAPowerSupplyMatrixImportView, EACopyControlUnitsView

router = DefaultRouter()
router.register(r'constructor', ConstructorViewSet, basename='ea-constructor')

from .utils.universal_renderer import UniversalTemplateRenderer
renderer = UniversalTemplateRenderer()
urlpatterns = [
    path('', include(router.urls)),
    path('admin/power-supply-matrix/', EAPowerSupplyMatrixView.as_view(), name='ea_power_supply_matrix'),
    path('admin/power-supply-matrix/export/', EAPowerSupplyMatrixExportView.as_view(), name='ea_power_supply_export'),
    path('admin/power-supply-matrix/import/', EAPowerSupplyMatrixImportView.as_view(), name='ea_power_supply_import'),
    path('admin/copy-control-units/', EACopyControlUnitsView.as_view(), name='ea_copy_control_units'),
    path('options/', EAOptionAPIView.as_view(), name='get_options'),
path(
        'description/<int:instance_id>/html/',
        renderer.response_json_html,
        name='description_json_html'
    ),
    path(
        'description/<int:instance_id>/docx/',
        renderer.response_docx,
        name='description_docx'
    ),
]