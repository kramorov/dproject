#core/urls.py
from django.urls import path
from .views import UniversalAPIView, DebugAPIView

urlpatterns = [
    path('', UniversalAPIView.as_view(), name='universal_api'),  # Изменил name тоже
path('debug/', DebugAPIView.as_view(), name='debug_api'),  # для теста
]