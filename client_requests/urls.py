# client_requests/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from client_requests.api.views import (
    ClientRequestViewSet,
    ClientRequestItemViewSet,
    RequestItemTypeViewSet,
)

router = DefaultRouter()
router.register(r'requests', ClientRequestViewSet, basename='cr-request')
router.register(r'items', ClientRequestItemViewSet, basename='cr-item')
router.register(r'item-types', RequestItemTypeViewSet, basename='cr-item-type')

urlpatterns = []
urlpatterns += router.urls
