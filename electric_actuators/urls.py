# electric_actuators/urls.py
from django.urls import path
from .api.views import EAOptionAPIView
from .utils.universal_renderer import UniversalTemplateRenderer
renderer = UniversalTemplateRenderer()
urlpatterns = [
    path('options/', EAOptionAPIView.as_view(), name='get_options'),
path(
        'api/description/<int:instance_id>/html/',
        renderer.response_json_html,
        name='description_json_html'
    ),
    path(
        'api/description/<int:instance_id>/docx/',
        renderer.response_docx,
        name='description_docx'
    ),
]