# myapp/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MyModelViewSet, IPChoiceViewSet, TempChoiceViewSet

router = DefaultRouter()
router.register(r'mymodels', MyModelViewSet)
router.register(r'ipchoices', IPChoiceViewSet)
router.register(r'tempchoices', TempChoiceViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
