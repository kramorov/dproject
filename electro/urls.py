# myapp/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ElectroModelViewSet, IPChoiceViewSet

router = DefaultRouter()
router.register(r'mymodels', ElectroModelViewSet)
router.register(r'ipchoices', IPChoiceViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
