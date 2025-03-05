from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'brands', views.BrandsViewSet)
router.register(r'producers', views.ProducerViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
