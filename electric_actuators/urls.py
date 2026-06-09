# electric_actuators/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api.views import EAOptionAPIView
from .api.views_constructor import ConstructorViewSet

router = DefaultRouter()
router.register(r'constructor', ConstructorViewSet, basename='ea-constructor')

from .utils.universal_renderer import UniversalTemplateRenderer
renderer = UniversalTemplateRenderer()
urlpatterns = [
    path('', include(router.urls)),
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