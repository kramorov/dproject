from django.urls import path
from .views import UniversalAPIView

urlpatterns = [
    path('core/', UniversalAPIView.as_view(), name='core-api'),
]