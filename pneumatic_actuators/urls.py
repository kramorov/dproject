# pneumatic_actuators/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api.views import OptionAPIView
from .api.views_constructor import ConstructorViewSet

router = DefaultRouter()
router.register(r'constructor', ConstructorViewSet, basename='constructor')

urlpatterns = [
    path('options/', OptionAPIView.as_view(), name='get_options'),
    path('', include(router.urls)),
]
