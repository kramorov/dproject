from django.urls import path

from .views import EttDecodeView

urlpatterns = [
    path('decode/', EttDecodeView.as_view(), name='ett_decode'),
]
