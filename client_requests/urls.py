# client_requests/urls.py
from django.urls import path
from client_requests.views.requirement_api import RequirementsSchemaView, RequirementsPreviewView

urlpatterns = [
    path('requirements/schema/', RequirementsSchemaView.as_view(), name='requirements_schema'),
    path('requirements/preview/', RequirementsPreviewView.as_view(), name='requirements_preview'),
]
