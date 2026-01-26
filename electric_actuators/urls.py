# electric_actuators/urls.py
from django.urls import path
from .api.views import EAOptionAPIView

urlpatterns = [
    path('options/', EAOptionAPIView.as_view(), name='get_options'),
]