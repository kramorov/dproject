#core/urls.py
from django.urls import path
from .views import UniversalAPIView

urlpatterns = [
    path('', UniversalAPIView.as_view(), name='universal_api'),  # Изменил name тоже
]