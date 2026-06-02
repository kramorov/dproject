#core/urls.py
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from .views import UniversalAPIView, DebugAPIView, ExdStructureView, ExdCompatibleView

urlpatterns = [
    path('', csrf_exempt(UniversalAPIView.as_view()), name='universal_api'),
    path('debug/', DebugAPIView.as_view(), name='debug_api'),
    path('exd/structure/', ExdStructureView.as_view(), name='exd_structure'),
    path('exd/compatible/', ExdCompatibleView.as_view(), name='exd_compatible'),
]