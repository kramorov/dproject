# myapp/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CableGlandBodyMaterialViewSet, CableGlandItemViewSet, CableGlandModelLineViewSet, \
    CableGlandItemTypeViewSet

router = DefaultRouter()
router.register(r'cable-glands-model-lines', CableGlandModelLineViewSet)
router.register(r'cable-glands-type', CableGlandItemTypeViewSet)
router.register(r'cable-glands-materials', CableGlandBodyMaterialViewSet)

router.register(r'cable-glands', CableGlandItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
