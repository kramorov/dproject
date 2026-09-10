# cable_glands/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from cable_glands.api.views_constructor import CableGlandConstructorViewSet

router = DefaultRouter()
router.register(r'constructor', CableGlandConstructorViewSet, basename='cg-constructor')

urlpatterns = [
    path('', include(router.urls)),
]
