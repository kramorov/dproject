from django.urls import path
from .api.views import OptionAPIView

urlpatterns = [
    path('api/options/', OptionAPIView.as_view(), name='get_options'),
]