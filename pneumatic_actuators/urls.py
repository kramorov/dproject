# pneumatic_actuators/urls.py
from django.urls import path
from .api.views import OptionAPIView

urlpatterns = [
    path('options/', OptionAPIView.as_view(), name='get_options'),
    # Убираем ModelLineDetailView - он не нужен!
    # Убираем все остальные маршруты, которые покрываются UniversalAPIView
]