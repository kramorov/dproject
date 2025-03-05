from django.urls import path
from .views import ValveModelDataAPIView, ValveLineAPIView

urlpatterns = [
    path('valve-model-data/<int:pk>/', ValveModelDataAPIView.as_view(), name='valve_model_data_detail'),
    path('valve-line/<int:pk>/', ValveLineAPIView.as_view(), name='valve_line_detail'),
]